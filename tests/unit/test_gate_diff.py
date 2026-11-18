"""REQ-054: fail-closed changed-file gate mapping and base resolution."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import gate_diff  # noqa: E402


@pytest.fixture(scope="module")
def gate_map():
    return gate_diff.load_gate_map()


def _test_files() -> list[str]:
    return sorted(
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in (ROOT / "tests").rglob("test_*.py")
    )


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    )


def _init_git_repo(root: Path) -> tuple[Path, str]:
    repo = root / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "gate@example.invalid")
    _git(repo, "config", "user.name", "gate test")
    (repo / "base.txt").write_text("base\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    return repo, _git(repo, "rev-parse", "HEAD").stdout.strip()


# --- mapping coverage -------------------------------------------------------


def test_every_engine_role_has_a_mapping(gate_map) -> None:
    actual = sorted(path.name for path in (ROOT / "ansible" / "roles").iterdir() if path.is_dir())
    assert actual, "ansible/roles is empty"
    assert sorted(gate_map["roles"]) == actual


def test_all_mapped_tests_exist(gate_map) -> None:
    mapped = set(gate_map.get("role_common_tests", []))
    for tests in gate_map["roles"].values():
        mapped.update(tests)
    for group in gate_map["groups"].values():
        mapped.update(group.get("tests", []))
    assert mapped
    missing = sorted(path for path in mapped if not (ROOT / path).is_file())
    assert missing == []


def test_every_test_file_is_reachable(gate_map) -> None:
    """Mapping coverage against the actual tests tree, not a hand-copied list."""
    referenced = set(gate_map.get("role_common_tests", []))
    for tests in gate_map["roles"].values():
        referenced.update(tests)
    for group in gate_map["groups"].values():
        referenced.update(group.get("tests", []))

    actual = set(_test_files())
    uncovered = sorted(actual - referenced)
    assert uncovered == [], f"test files with no explicit role/group mapping: {uncovered}"

    # And each of those references does resolve to itself through the rules.
    for test in sorted(actual):
        plan = gate_diff.build_plan([test], gate_map)
        assert not plan.full_suite, test
        assert test in plan.tests, test


def test_every_role_path_maps_to_its_role_tests(gate_map) -> None:
    for role, expected in gate_map["roles"].items():
        plan = gate_diff.build_plan([f"ansible/roles/{role}/tasks/main.yml"], gate_map)
        assert not plan.full_suite, role
        for test in expected:
            assert test in plan.tests, (role, test)
        # The seam/fixture assertions travel with every role change.
        for test in gate_map.get("role_common_tests", []):
            assert test in plan.tests, (role, test)


def test_every_role_playbook_maps_to_a_role(gate_map) -> None:
    playbooks = sorted(path.name for path in (ROOT / "ansible" / "playbooks").glob("*.yml"))
    playbooks += sorted(path.name for path in (ROOT / "ansible" / "playbooks").glob("*.yaml"))
    for playbook in playbooks:
        path = f"ansible/playbooks/{playbook}"
        plan = gate_diff.build_plan([path], gate_map)
        assert not plan.full_suite, path
        assert plan.tests, path


# --- scoping / fallbacks ----------------------------------------------------


def test_role_change_is_scoped(gate_map) -> None:
    plan = gate_diff.build_plan(["ansible/roles/verify/tasks/main.yml"], gate_map)
    assert not plan.full_suite
    assert "tests/unit/test_verify_role.py" in plan.tests
    assert "tests/unit/test_btop_config_role.py" not in plan.tests
    assert plan.test_count < len(_test_files())
    assert {"ruff", "docs-check"} <= set(plan.checks)


def test_role_vars_change_triggers_pin_audit(gate_map) -> None:
    plan = gate_diff.build_plan(["ansible/roles/verify/vars/main.yml"], gate_map)
    assert not plan.full_suite
    assert "pin-audit" in plan.checks


def test_role_only_run_does_not_touch_the_whole_suite(gate_map) -> None:
    plan = gate_diff.role_plan("verify", gate_map)
    assert not plan.full_suite
    assert plan.role == "verify"
    assert plan.tests == tuple(
        dict.fromkeys(
            gate_map["roles"]["verify"] + gate_map.get("role_common_tests", [])
        )
    )
    assert "tests/unit/test_btop_config_role.py" not in plan.tests
    assert {"ruff", "docs-check", "pin-audit"} <= set(plan.checks)


def test_unknown_role_fails_closed(gate_map) -> None:
    with pytest.raises(gate_diff.GateError, match="no tests for role"):
        gate_diff.role_plan("does_not_exist", gate_map)


def test_unknown_path_falls_back_to_full_suite(gate_map) -> None:
    plan = gate_diff.build_plan(["mystery/unknown.txt"], gate_map)
    assert plan.full_suite
    assert "mystery/unknown.txt" in (plan.fallback_reason or "")
    assert "ruff" in plan.checks and "docs-check" in plan.checks


@pytest.mark.parametrize(
    "path",
    [
        "Makefile",
        "pyproject.toml",
        "uv.lock",
        "scripts/gate-map.yaml",
        "scripts/gate_diff.py",
        "scripts/ci-gates-parity.py",
        ".github/workflows/gates.yml",
    ],
)
def test_gate_sensitive_paths_fall_back_to_full_suite(gate_map, path: str) -> None:
    plan = gate_diff.build_plan([path], gate_map)
    assert plan.full_suite, path
    assert plan.fallback_reason
    assert path in plan.fallback_reason or "gate-sensitive" in plan.fallback_reason


def test_docs_only_change_uses_docs_check_not_pytest(gate_map) -> None:
    plan = gate_diff.build_plan(["tickets/REQ-999/example.md"], gate_map)
    assert not plan.full_suite
    assert plan.tests == ()
    assert "docs-check" in plan.checks


def test_test_helper_file_falls_back(gate_map) -> None:
    plan = gate_diff.build_plan(["tests/unit/assets_templates.py"], gate_map)
    assert not plan.full_suite
    assert "tests/unit/test_template_vars_parity.py" in plan.tests


def test_pin_audit_triggers_only_for_pin_sensitive_paths(gate_map) -> None:
    fixture = gate_diff.build_plan(
        ["tests/fixtures/composition/dotfiles/provisioning/assets.yaml"], gate_map
    )
    assert "pin-audit" in fixture.checks
    docs = gate_diff.build_plan(["README.md"], gate_map)
    assert "pin-audit" not in docs.checks


def test_plan_is_deterministic(gate_map) -> None:
    paths = ["ansible/roles/verify/tasks/main.yml", "src/provisioning/domain/models.py"]
    first = gate_diff.build_plan(paths, gate_map)
    second = gate_diff.build_plan(reversed(paths), gate_map)
    assert first.tests == second.tests
    assert first.checks == second.checks
    assert first.full_suite == second.full_suite


def test_describe_prints_base_and_fallback(gate_map) -> None:
    plan = gate_diff.build_plan(
        ["mystery/unknown.txt"], gate_map, base="origin/main", base_sha="abc123"
    )
    text = gate_diff.describe(plan)
    assert "resolved base: origin/main (merge-base abc123)" in text
    assert "DEV FEEDBACK ONLY" in text
    assert "FALLBACK: full fast suite" in text
    assert "mystery/unknown.txt" in text


# --- git change collection / base resolution -------------------------------


def test_changed_paths_include_committed_worktree_staged_and_untracked(tmp_path) -> None:
    repo, base = _init_git_repo(tmp_path)

    (repo / "committed.txt").write_text("committed\n")
    _git(repo, "add", "committed.txt")
    _git(repo, "commit", "-m", "committed change")

    (repo / "base.txt").write_text("working tree edit\n")
    (repo / "staged.txt").write_text("staged\n")
    _git(repo, "add", "staged.txt")
    (repo / "untracked.txt").write_text("untracked\n")

    changed = gate_diff.collect_changed_paths(repo, base)
    assert set(changed) == {
        "base.txt",
        "committed.txt",
        "staged.txt",
        "untracked.txt",
    }


def test_base_resolution_fails_clearly_without_a_base(tmp_path) -> None:
    repo, _ = _init_git_repo(tmp_path)
    _git(repo, "branch", "-m", "main", "trunk")
    if "origin" in _git(repo, "remote").stdout.split():
        _git(repo, "remote", "remove", "origin")
    with pytest.raises(gate_diff.GateError) as excinfo:
        gate_diff.resolve_base(repo)
    message = str(excinfo.value)
    assert "cannot resolve BASE" in message
    assert "origin/main" in message and "main" in message
    assert "BASE=<ref>" in message


def test_explicit_missing_base_fails_clearly(tmp_path) -> None:
    repo, _ = _init_git_repo(tmp_path)
    with pytest.raises(gate_diff.GateError, match="not a commit"):
        gate_diff.resolve_base(repo, "does-not-exist")


def test_base_resolution_returns_the_explicit_ref(tmp_path) -> None:
    repo, _ = _init_git_repo(tmp_path)
    ref, sha = gate_diff.resolve_base(repo, "main")
    assert ref == "main"
    assert sha == _git(repo, "rev-parse", "HEAD").stdout.strip()


# --- authoritative gates stay untouched ------------------------------------


def test_gates_list_is_unchanged() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    match = re.search(r"^GATES\s*:?=\s*(.+)$", makefile, re.MULTILINE)
    assert match is not None
    assert match.group(1).split() == ["test", "lint", "hermetic", "lock-check", "docs-check"]


def test_dev_targets_do_not_become_release_gates() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    gates_line = re.search(r"^GATES\s*:?=\s*(.+)$", makefile, re.MULTILINE)
    assert gates_line is not None
    assert "dev" not in gates_line.group(1).split()
    assert "\ndev:" in makefile
    assert "\ndev-hermetic:" in makefile
    assert "\ngates-diff:" in makefile
    assert "\ngates-role:" in makefile
