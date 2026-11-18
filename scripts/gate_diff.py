#!/usr/bin/env python3
"""Fail-closed changed-file gate for development feedback (REQ-054).

``make dev`` (and ``make gates-diff`` / ``make gates-role``) runs the cheap
global checks plus the tests selected by the explicit mapping in
``scripts/gate-map.yaml``. It is **feedback only**: ``make gates`` and CI remain
the release authority.

The gate fails closed. These inputs run the full fast suite instead of a narrow
selection:

* the Makefile, pyproject.toml, uv.lock, or a gate script changed;
* an unknown path changed;
* a changed path resolved to zero pytest tests (except docs-only changes, whose
  mapped check is ``docs-check``);
* an Ansible role or role playbook is missing from the map.

Changed paths are collected from the merge-base with ``BASE`` (default
``origin/main``, then ``main``) plus the working tree, the index, and untracked
files. The resolved base is always printed.

Usage::

    python3 scripts/gate_diff.py
    python3 scripts/gate_diff.py --base origin/main
    python3 scripts/gate_diff.py --role verify
    python3 scripts/gate_diff.py --dry-run
    python3 scripts/gate_diff.py --hermetic
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
GATE_MAP_PATH = ROOT / "scripts" / "gate-map.yaml"
FAST_MARKER = "not integration and not container_target"
DEFAULT_BASES = ("origin/main", "main")


class GateError(RuntimeError):
    """A fail-closed gate configuration or base-resolution error."""


@dataclass(frozen=True)
class PathMapping:
    """One changed path and the checks/tests the map selected for it."""

    path: str
    rule: str
    tests: tuple[str, ...] = ()
    checks: tuple[str, ...] = ()
    full_suite: bool = False
    reason: str | None = None


@dataclass
class Plan:
    """A complete, deterministic gate plan."""

    changed: tuple[str, ...]
    mappings: tuple[PathMapping, ...]
    tests: tuple[str, ...]
    checks: tuple[str, ...]
    full_suite: bool = False
    fallback_reason: str | None = None
    base: str | None = None
    base_sha: str | None = None
    role: str | None = None

    def __post_init__(self) -> None:
        if self.full_suite:
            self.fallback_reason = self.fallback_reason or "full fast suite requested"

    @property
    def test_count(self) -> int:
        return len(self.tests)


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GateError(f"gate map not found: {path}")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise GateError(f"{path}: expected a mapping at the top level")
    return loaded


def load_gate_map(path: Path | None = None) -> dict[str, Any]:
    """Load and minimally validate the explicit mapping file."""
    data = _read_yaml(path or GATE_MAP_PATH)
    if data.get("version") != 1:
        raise GateError(f"{path or GATE_MAP_PATH}: unsupported gate-map version")
    roles = data.get("roles")
    if not isinstance(roles, dict) or not roles:
        raise GateError(f"{path or GATE_MAP_PATH}: `roles` must be a non-empty mapping")
    groups = data.get("groups") or {}
    if not isinstance(groups, dict):
        raise GateError(f"{path or GATE_MAP_PATH}: `groups` must be a mapping")
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        raise GateError(f"{path or GATE_MAP_PATH}: `rules` must be a non-empty list")
    return data


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise GateError(f"expected a list, got {type(value).__name__}")
    return tuple(str(item) for item in value)


def _group_tests(name: str, data: dict[str, Any]) -> tuple[str, ...]:
    groups = data["groups"]
    group = groups.get(name)
    if not isinstance(group, dict):
        raise GateError(f"gate map names unknown group `{name}`")
    tests = list(_as_tuple(group.get("tests")))
    if group.get("all_roles"):
        for role_tests in data["roles"].values():
            tests.extend(_as_tuple(role_tests))
    return tuple(dict.fromkeys(tests))


def _role_tests(role: str, data: dict[str, Any]) -> tuple[str, ...]:
    roles = data["roles"]
    if role not in roles:
        raise GateError(f"gate map has no tests for role `{role}`")
    tests = list(_as_tuple(roles[role]))
    tests.extend(_as_tuple(data.get("role_common_tests")))
    return tuple(dict.fromkeys(tests))


def _playbook_role_tests(playbook: str, data: dict[str, Any]) -> tuple[str, ...]:
    stem = Path(playbook).stem
    role = stem.replace("-", "_")
    if role not in data["roles"]:
        raise GateError(f"gate map has no role for playbook `{playbook}`")
    tests = list(_role_tests(role, data))
    tests.append("tests/unit/test_bootstrap_playbook.py")
    return tuple(dict.fromkeys(tests))


def _matching_rule(path: str, rules: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    for rule in rules:
        if "match" in rule and fnmatch.fnmatchcase(path, str(rule["match"])):
            return rule
        if "prefix" in rule and path.startswith(str(rule["prefix"])):
            return rule
    return None


def _rule_label(rule: dict[str, Any]) -> str:
    if "match" in rule:
        return f"match:{rule['match']}"
    return f"prefix:{rule['prefix']}"


def _is_pytest_file(path: str) -> bool:
    name = Path(path).name
    return name.startswith("test_") and name.endswith(".py")


def _map_path(path: str, data: dict[str, Any]) -> PathMapping:
    rule = _matching_rule(path, data["rules"])
    if rule is None:
        return PathMapping(
            path=path,
            rule="unmatched",
            full_suite=True,
            reason=f"unknown changed path `{path}`",
        )

    label = _rule_label(rule)
    if rule.get("full_suite"):
        reason = str(rule.get("reason") or f"gate-sensitive path `{path}`")
        return PathMapping(
            path=path,
            rule=label,
            full_suite=True,
            reason=f"{reason}: `{path}`",
        )

    tests: list[str] = []
    checks: list[str] = []

    if rule.get("role"):
        parts = path.split("/")
        if len(parts) < 3 or parts[0] != "ansible" or parts[1] != "roles":
            return PathMapping(path, label, full_suite=True, reason=f"bad role path `{path}`")
        role = parts[2]
        try:
            tests.extend(_role_tests(role, data))
        except GateError as exc:
            return PathMapping(path, label, full_suite=True, reason=str(exc))

    if rule.get("playbook"):
        try:
            tests.extend(_playbook_role_tests(path, data))
        except GateError as exc:
            return PathMapping(path, label, full_suite=True, reason=str(exc))

    if rule.get("self"):
        if not _is_pytest_file(path):
            return PathMapping(
                path,
                label,
                full_suite=True,
                reason=f"`{path}` is a test support file, not a pytest module",
            )
        tests.append(path)

    for group in rule.get("groups", []) or []:
        try:
            tests.extend(_group_tests(str(group), data))
        except GateError as exc:
            return PathMapping(path, label, full_suite=True, reason=str(exc))

    checks.extend(_as_tuple(rule.get("checks")))

    deduped_tests = tuple(dict.fromkeys(tests))
    deduped_checks = tuple(dict.fromkeys(checks))
    if not deduped_tests and not deduped_checks:
        return PathMapping(
            path=path,
            rule=label,
            full_suite=True,
            reason=f"changed path `{path}` mapped to zero tests or checks",
        )
    return PathMapping(path, label, tests=deduped_tests, checks=deduped_checks)


def _pin_audit_needed(paths: Iterable[str], data: dict[str, Any]) -> bool:
    patterns = _as_tuple(data.get("pin_audit_when"))
    return any(fnmatch.fnmatchcase(path, pattern) for path in paths for pattern in patterns)


def build_plan(
    changed_paths: Iterable[str],
    data: dict[str, Any],
    *,
    base: str | None = None,
    base_sha: str | None = None,
    role: str | None = None,
) -> Plan:
    """Map a change set to tests/checks. Deterministic and fail-closed."""
    changed = tuple(sorted({p.strip().strip("/") for p in changed_paths if p.strip()}))
    mappings = tuple(_map_path(path, data) for path in changed)

    full_reason: str | None = None
    for mapping in mappings:
        if mapping.full_suite:
            full_reason = mapping.reason
            break

    tests: list[str] = []
    checks: list[str] = []
    for mapping in mappings:
        tests.extend(mapping.tests)
        checks.extend(mapping.checks)

    checks = list(_as_tuple(data.get("global_checks"))) + checks
    if _pin_audit_needed(changed, data):
        checks.append("pin-audit")

    return Plan(
        changed=changed,
        mappings=mappings,
        tests=tuple(dict.fromkeys(tests)),
        checks=tuple(dict.fromkeys(checks)),
        full_suite=full_reason is not None,
        fallback_reason=full_reason,
        base=base,
        base_sha=base_sha,
        role=role,
    )


def role_plan(role: str, data: dict[str, Any]) -> Plan:
    """Plan a role-only run without consulting the diff."""
    tests = _role_tests(role, data)
    checks = list(_as_tuple(data.get("global_checks")))
    # Role vars are a pin-bearing surface; keep the pin check cheap but present.
    checks.append("pin-audit")
    return Plan(
        changed=(),
        mappings=(PathMapping(path=f"role:{role}", rule="role", tests=tests),),
        tests=tests,
        checks=tuple(dict.fromkeys(checks)),
        role=role,
    )


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )


def resolve_base(root: Path, requested: str | None = None) -> tuple[str, str]:
    """Resolve BASE explicitly and return ``(ref, merge-base-sha)``.

    A failure raises GateError rather than silently diffing against an empty
    tree; the gate must never turn "cannot resolve main" into "no changes".
    """
    candidates = (requested,) if requested else DEFAULT_BASES
    attempts: list[str] = []
    for candidate in candidates:
        if not candidate:
            continue
        verify = _git(root, "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}")
        if verify.returncode != 0:
            attempts.append(f"{candidate} (not a commit)")
            continue
        merge = _git(root, "merge-base", candidate, "HEAD")
        if merge.returncode != 0 or not merge.stdout.strip():
            detail = merge.stderr.strip() or "no common ancestor with HEAD"
            attempts.append(f"{candidate} ({detail})")
            continue
        return candidate, merge.stdout.strip()
    tried = ", ".join(attempts) if attempts else "no candidates"
    raise GateError(
        "cannot resolve BASE "
        f"({tried}); pass BASE=<ref> (for example BASE=origin/main) "
        "or create/fetch the default branch"
    )


def collect_changed_paths(root: Path, base_sha: str) -> tuple[str, ...]:
    """Committed-since-merge-base + working tree + staged + untracked paths."""
    commands = (
        ("committed", ["diff", "--name-only", "--diff-filter=ACMRTUXB", f"{base_sha}...HEAD"]),
        ("working-tree", ["diff", "--name-only", "--diff-filter=ACMRTUXB"]),
        ("staged", ["diff", "--name-only", "--diff-filter=ACMRTUXB", "--cached"]),
        ("untracked", ["ls-files", "--others", "--exclude-standard"]),
    )
    paths: list[str] = []
    for label, args in commands:
        result = _git(root, *args)
        if result.returncode != 0:
            raise GateError(f"git {label} failed: {result.stderr.strip() or result.returncode}")
        paths.extend(line.strip() for line in result.stdout.splitlines() if line.strip())
    return tuple(sorted({path.replace(os.sep, "/").strip("/") for path in paths}))


def describe(plan: Plan) -> str:
    lines = [
        "gate-diff: DEV FEEDBACK ONLY — `make gates`/CI remain the release authority",
    ]
    if plan.role:
        lines.append(f"role: {plan.role} (diff ignored; explicit role target)")
    else:
        lines.append(f"resolved base: {plan.base} (merge-base {plan.base_sha})")
        lines.append(f"changed paths ({len(plan.changed)}):")
        for path in plan.changed:
            lines.append(f"  - {path}")
    if plan.full_suite:
        lines.append(f"FALLBACK: full fast suite — {plan.fallback_reason}")
    lines.append("mapping:")
    if not plan.mappings:
        lines.append("  (no changed paths)")
    for mapping in plan.mappings:
        target = "FULL FAST SUITE" if mapping.full_suite else (
            ", ".join(mapping.tests) or f"checks only: {', '.join(mapping.checks)}"
        )
        lines.append(f"  {mapping.path} [{mapping.rule}] -> {target}")
    lines.append(f"global checks: {', '.join(plan.checks)}")
    if plan.full_suite:
        lines.append("pytest: full fast suite")
    else:
        lines.append(f"pytest files ({plan.test_count}):")
        for test in plan.tests:
            lines.append(f"  - {test}")
    return "\n".join(lines)


def _run(cmd: list[str], *, root: Path, env: dict[str, str] | None = None) -> int:
    print(f"+ {shlex.join(cmd)}")
    return subprocess.run(cmd, cwd=root, env=env, check=False).returncode


def _ruff(root: Path) -> int:
    return _run([sys.executable, "-m", "ruff", "check", "src", "tests"], root=root)


def _docs_check(root: Path) -> int:
    return _run(["make", "docs-check"], root=root)


def _pin_audit(root: Path) -> int:
    return _run([sys.executable, "scripts/pin-audit.py"], root=root)


def _run_checks(plan: Plan, root: Path) -> list[str]:
    failures: list[str] = []
    runners = {
        "ruff": _ruff,
        "docs-check": _docs_check,
        "pin-audit": _pin_audit,
    }
    for check in plan.checks:
        runner = runners.get(check)
        if runner is None:
            failures.append(f"unknown check `{check}`")
            continue
        if runner(root) != 0:
            failures.append(check)
    return failures


def _pytest_targets(plan: Plan, root: Path, *, absolute: bool) -> list[str]:
    if plan.full_suite:
        return [str(root / "tests")] if absolute else ["tests"]
    if not plan.tests:
        raise GateError("plan has no pytest files and is not a full-suite fallback")
    return [str(root / test) if absolute else test for test in plan.tests]


def _run_pytest(plan: Plan, root: Path) -> int:
    cmd = [sys.executable, "-m", "pytest", "-q", "-m", FAST_MARKER, *_pytest_targets(
        plan, root, absolute=False
    )]
    return _run(cmd, root=root)


def _run_pytest_hermetic(plan: Plan, root: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="gate-diff-") as tmp:
        tmp_path = Path(tmp)
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        for name in ("home", "config", "cache", "data", "state"):
            (tmp_path / name).mkdir()
        env = os.environ.copy()
        env.update(
            HOME=str(tmp_path / "home"),
            XDG_CONFIG_HOME=str(tmp_path / "config"),
            XDG_CACHE_HOME=str(tmp_path / "cache"),
            XDG_DATA_HOME=str(tmp_path / "data"),
            XDG_STATE_HOME=str(tmp_path / "state"),
            TMPDIR=str(tmp_path),
            PATH=f"{root / '.venv' / 'bin'}:{env.get('PATH', '')}",
            ANSIBLE_COLLECTIONS_PATH=str(root / ".collections"),
            PYTHONPATH=f"{root / 'src'}:{root}",
        )
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-m",
            FAST_MARKER,
            "-c",
            str(root / "pyproject.toml"),
            "--rootdir",
            str(root),
            *_pytest_targets(plan, root, absolute=True),
        ]
        print(f"+ (hermetic, cwd={cwd}) {shlex.join(cmd)}")
        return subprocess.run(cmd, cwd=cwd, env=env, check=False).returncode


def execute(plan: Plan, root: Path, *, dry_run: bool = False, hermetic: bool = False) -> int:
    print(describe(plan), flush=True)
    if dry_run:
        print("dry-run: no checks or tests executed")
        return 0

    failures = _run_checks(plan, root)
    if failures:
        print(f"FAIL checks: {', '.join(failures)}", file=sys.stderr)
        return 1

    rc = _run_pytest_hermetic(plan, root) if hermetic else _run_pytest(plan, root)
    if rc != 0:
        print(f"FAIL pytest (exit {rc})", file=sys.stderr)
        return rc
    print("PASS gate-diff (dev feedback only; run `make gates` before release)")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default=None,
        help="ref to diff against (default: origin/main, then main)",
    )
    parser.add_argument(
        "--role",
        default=None,
        help="run one Ansible role's mapped tests instead of a diff",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="repository root (defaults to this script's checkout)",
    )
    parser.add_argument("--dry-run", action="store_true", help="print the plan and exit")
    parser.add_argument(
        "--hermetic",
        action="store_true",
        help="run selected tests with empty HOME/XDG and a foreign cwd",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root = Path(args.root).resolve() if args.root else ROOT
    try:
        data = load_gate_map(root / "scripts" / "gate-map.yaml")
        if args.role:
            plan = role_plan(args.role, data)
        else:
            base, sha = resolve_base(root, args.base)
            changed = collect_changed_paths(root, sha)
            plan = build_plan(changed, data, base=base, base_sha=sha)
    except GateError as exc:
        print(f"gate-diff: {exc}", file=sys.stderr)
        if args.role:
            try:
                roles = ", ".join(sorted(load_gate_map(root / "scripts" / "gate-map.yaml")["roles"]))
                print(f"known roles: {roles}", file=sys.stderr)
            except GateError:
                pass
        return 2

    try:
        return execute(plan, root, dry_run=args.dry_run, hermetic=args.hermetic)
    except GateError as exc:
        print(f"gate-diff: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
