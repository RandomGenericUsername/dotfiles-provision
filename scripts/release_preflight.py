#!/usr/bin/env python3
"""Read-only release preflight (REQ-055).

Run this **before** creating a release tag. It answers one question: is this
checkout ready to be tagged? It never creates a tag, never pushes, never applies
anything, and never runs the full test suite.

The checks are deliberately split so a failure names the exact surface:

* clean worktree and the expected release branch;
* one consistent release version in ``pyproject.toml`` and
  ``src/provisioning/__init__.py`` (when the package exposes ``__version__``);
* the tag is supplied or derived from the package version, matches it, and does
  not already exist locally or on ``origin``;
* ``CHANGELOG.md`` has an entry for the version;
* the lock file, pin audit, CI/gate parity, and docs checks pass;
* a small set of release-sensitive tests pass (not the full suite).

Usage::

    python3 scripts/release_preflight.py
    python3 scripts/release_preflight.py --tag v0.1.89
    python3 scripts/release_preflight.py --branch main
    make release-preflight TAG=v0.1.89
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
import tomllib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG_RE = re.compile(r"^v\d+\.\d+\.\d+$")
INIT_VERSION_RE = re.compile(
    r"""^__version__\s*=\s*["']([^"']+)["']""",
    re.MULTILINE,
)

# Release-sensitive, cheap checks. This is not a substitute for `make test` or
# `make hermetic`; it catches the fixture/contract drifts that have caused tag
# churn (quoted ExecStart, expac chronology, packaged Ansible tree, seam).
TARGETED_TESTS = (
    "tests/test_packaging.py",
    "tests/unit/test_gloview_units.py",
    "tests/unit/test_gloview_plugin_role.py",
    "tests/unit/test_compositor_skeleton_configs.py",
    "tests/unit/test_composition_seam.py",
    "tests/unit/test_template_vars_parity.py",
)

CommandRunner = Callable[[Sequence[str], Path], int]
TagProbe = Callable[[Path, str], bool]


class PreflightError(RuntimeError):
    """A check could not be evaluated; preflight fails closed."""


@dataclass(frozen=True)
class Check:
    """One named preflight check and its outcome."""

    name: str
    ok: bool
    detail: str


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_command(cmd: Sequence[str], root: Path) -> int:
    """Run a command, echoing it and its output for an actionable failure."""
    print(f"+ {shlex.join(cmd)}", flush=True)
    try:
        proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True, check=False)
    except OSError as exc:
        print(f"  cannot execute: {exc}", file=sys.stderr)
        return 127
    if proc.stdout.strip():
        print(proc.stdout.rstrip())
    if proc.stderr.strip():
        print(proc.stderr.rstrip(), file=sys.stderr)
    return proc.returncode


def _local_tag_exists(root: Path, tag: str) -> bool:
    proc = _git(root, "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}")
    if proc.returncode not in (0, 1):
        raise PreflightError(proc.stderr.strip() or f"git rev-parse exited {proc.returncode}")
    return proc.returncode == 0


def _remote_tag_exists(root: Path, tag: str) -> bool:
    proc = _git(
        root,
        "ls-remote",
        "--tags",
        "origin",
        f"refs/tags/{tag}",
        f"refs/tags/{tag}^{{}}",
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or f"git ls-remote exited {proc.returncode}"
        raise PreflightError(f"cannot query origin: {detail}")
    return bool(proc.stdout.strip())


def read_pyproject_version(root: Path) -> str:
    path = root / "pyproject.toml"
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PreflightError(f"{path}: not found") from exc
    except tomllib.TOMLDecodeError as exc:
        raise PreflightError(f"{path}: invalid TOML: {exc}") from exc
    version = data.get("project", {}).get("version")
    if not isinstance(version, str) or not version.strip():
        raise PreflightError(
            "pyproject.toml has no static [project].version; cannot derive TAG (pass TAG=vX.Y.Z)"
        )
    return version.strip()


def read_init_version(root: Path) -> str | None:
    path = root / "src" / "provisioning" / "__init__.py"
    if not path.is_file():
        return None
    match = INIT_VERSION_RE.search(path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def check_worktree(root: Path) -> Check:
    proc = _git(root, "status", "--porcelain")
    if proc.returncode != 0:
        return Check("worktree", False, proc.stderr.strip() or "git status failed")
    dirty = [line for line in proc.stdout.splitlines() if line.strip()]
    if dirty:
        preview = ", ".join(line[3:] if len(line) > 3 else line for line in dirty[:5])
        more = f" (+{len(dirty) - 5} more)" if len(dirty) > 5 else ""
        return Check("worktree", False, f"worktree is dirty: {preview}{more}")
    return Check("worktree", True, "clean")


def check_branch(root: Path, expected: str) -> Check:
    proc = _git(root, "branch", "--show-current")
    if proc.returncode != 0:
        return Check("branch", False, proc.stderr.strip() or "git branch failed")
    actual = proc.stdout.strip()
    if not actual:
        return Check("branch", False, f"detached HEAD; expected branch `{expected}`")
    if actual != expected:
        return Check("branch", False, f"on `{actual}`, expected `{expected}`")
    return Check("branch", True, actual)


def check_versions(root: Path) -> tuple[Check, str | None]:
    try:
        pyproject = read_pyproject_version(root)
    except PreflightError as exc:
        return Check("version", False, str(exc)), None

    init = read_init_version(root)
    if init is None:
        return (
            Check(
                "version",
                True,
                f"pyproject.toml={pyproject}; src/provisioning/__init__.py carries no __version__",
            ),
            pyproject,
        )
    if init != pyproject:
        return (
            Check(
                "version",
                False,
                f"pyproject.toml={pyproject} != src/provisioning/__init__.py={init}",
            ),
            pyproject,
        )
    return Check("version", True, f"pyproject.toml={pyproject}, __init__.py={init}"), pyproject


def resolve_tag(tag: str | None, version: str) -> tuple[Check, str | None]:
    expected = f"v{version}"
    if not TAG_RE.fullmatch(expected):
        return (
            Check(
                "tag",
                False,
                f"pyproject version {version} does not yield a vMAJOR.MINOR.PATCH tag",
            ),
            None,
        )
    if tag is None or not tag.strip():
        return Check("tag", True, f"derived from pyproject: {expected}"), expected
    tag = tag.strip()
    if not TAG_RE.fullmatch(tag):
        return Check("tag", False, f"`{tag}` is not vMAJOR.MINOR.PATCH"), None
    if tag != expected:
        return (
            Check(
                "tag",
                False,
                f"`{tag}` does not match pyproject version {version} (`{expected}`)",
            ),
            None,
        )
    return Check("tag", True, f"matches pyproject: {tag}"), tag


def check_local_tag(root: Path, tag: str, probe: TagProbe) -> Check:
    try:
        exists = probe(root, tag)
    except PreflightError as exc:
        return Check("tag-local", False, str(exc))
    if exists:
        return Check("tag-local", False, f"tag {tag} already exists locally")
    return Check("tag-local", True, f"{tag} absent locally")


def check_remote_tag(root: Path, tag: str, probe: TagProbe) -> Check:
    try:
        exists = probe(root, tag)
    except PreflightError as exc:
        return Check("tag-remote", False, str(exc))
    if exists:
        return Check("tag-remote", False, f"tag {tag} already exists on origin")
    return Check("tag-remote", True, f"{tag} absent on origin")


def check_changelog(root: Path, version: str) -> Check:
    path = root / "CHANGELOG.md"
    if not path.is_file():
        return Check("changelog", False, "CHANGELOG.md not found")
    text = path.read_text(encoding="utf-8")
    if re.search(rf"^##\s+{re.escape(version)}\s*$", text, re.MULTILINE):
        return Check("changelog", True, f"entry for {version}")
    return Check("changelog", False, f"CHANGELOG.md has no `## {version}` heading")


def check_command(
    name: str,
    cmd: Sequence[str],
    root: Path,
    runner: CommandRunner,
) -> Check:
    rc = runner(cmd, root)
    if rc == 0:
        return Check(name, True, f"`{shlex.join(cmd)}`")
    return Check(name, False, f"`{shlex.join(cmd)}` exited {rc}")


def run_preflight(
    root: Path,
    *,
    tag: str | None = None,
    branch: str = "main",
    runner: CommandRunner = _run_command,
    local_tag_exists: TagProbe = _local_tag_exists,
    remote_tag_exists: TagProbe = _remote_tag_exists,
) -> int:
    """Run every check in order, print a status line for each, and return 0/1."""
    print(f"release-preflight: root={root} tag={tag or '(derive)'} branch={branch}")
    results: list[Check] = [
        check_worktree(root),
        check_branch(root, branch),
    ]

    version_check, version = check_versions(root)
    results.append(version_check)

    resolved: str | None = None
    if version is None:
        results.append(Check("tag", False, "not checked: pyproject version unavailable"))
    else:
        tag_check, resolved = resolve_tag(tag, version)
        results.append(tag_check)

    if resolved is None:
        reason = "not checked: tag unresolved"
        results.append(Check("tag-local", False, reason))
        results.append(Check("tag-remote", False, reason))
    else:
        results.append(check_local_tag(root, resolved, local_tag_exists))
        results.append(check_remote_tag(root, resolved, remote_tag_exists))

    if version is None:
        results.append(Check("changelog", False, "not checked: version unavailable"))
    else:
        results.append(check_changelog(root, version))

    results.extend(
        [
            check_command("lock", ["uv", "lock", "--check"], root, runner),
            check_command("pin-audit", ["make", "pin-audit"], root, runner),
            check_command("ci-gates-parity", ["make", "ci-gates-parity"], root, runner),
            check_command("docs-check", ["make", "docs-check"], root, runner),
            check_command(
                "release-tests",
                [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS],
                root,
                runner,
            ),
        ]
    )

    width = max(len(result.name) for result in results)
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        print(f"{status} {result.name:<{width}}  {result.detail}")

    failed = [result for result in results if not result.ok]
    if failed:
        names = ", ".join(result.name for result in failed)
        print(f"release-preflight: FAIL ({len(failed)} check(s): {names})", file=sys.stderr)
        return 1
    print(f"release-preflight: PASS ({len(results)} checks); no tag was created")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tag",
        default=os.environ.get("TAG") or None,
        help="intended release tag (default: derived from pyproject.toml)",
    )
    parser.add_argument(
        "--branch",
        default=os.environ.get("BRANCH") or "main",
        help="expected release branch (default: main)",
    )
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="repository root (default: this checkout)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return run_preflight(
        Path(args.root).resolve(),
        tag=args.tag,
        branch=args.branch,
    )


if __name__ == "__main__":
    raise SystemExit(main())
