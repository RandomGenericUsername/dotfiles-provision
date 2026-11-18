"""REQ-055: read-only release preflight checks and failure messages."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import release_preflight  # noqa: E402


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True)


def _repo(
    root: Path,
    *,
    version: str = "1.2.3",
    init_version: str | None = "1.2.3",
    changelog: str | None = "## 1.2.3\n\nRelease notes.\n",
) -> Path:
    repo = root / "repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text(
        f'[project]\nname = "sample"\nversion = "{version}"\n', encoding="utf-8"
    )
    package = repo / "src" / "provisioning"
    package.mkdir(parents=True)
    init = '"""sample package."""\n\n'
    if init_version is not None:
        init += f'__version__ = "{init_version}"\n'
    (package / "__init__.py").write_text(init, encoding="utf-8")
    if changelog is not None:
        (repo / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "preflight@example.invalid")
    _git(repo, "config", "user.name", "preflight test")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    return repo


class FakeDeps:
    """Injected command/tag probes; tests never create or query real tags."""

    def __init__(self, *, local: bool = False, remote: bool = False, rc: int = 0) -> None:
        self.local = local
        self.remote = remote
        self.rc = rc
        self.commands: list[list[str]] = []

    def run(self, cmd, root: Path) -> int:  # noqa: ANN001 - matches CommandRunner
        self.commands.append(list(cmd))
        return self.rc

    def local_tag(self, root: Path, tag: str) -> bool:
        return self.local

    def remote_tag(self, root: Path, tag: str) -> bool:
        return self.remote


def _run(repo: Path, deps: FakeDeps, **kwargs) -> int:
    return release_preflight.run_preflight(
        repo,
        runner=deps.run,
        local_tag_exists=deps.local_tag,
        remote_tag_exists=deps.remote_tag,
        **kwargs,
    )


def test_success_is_read_only_and_reports_every_check(tmp_path, capsys) -> None:
    repo = _repo(tmp_path)
    deps = FakeDeps()

    rc = _run(repo, deps)

    out = capsys.readouterr().out
    assert rc == 0, out
    for name in (
        "worktree",
        "branch",
        "version",
        "tag",
        "tag-local",
        "tag-remote",
        "changelog",
        "lock",
        "pin-audit",
        "ci-gates-parity",
        "docs-check",
        "release-tests",
    ):
        assert f"PASS {name}" in out, name
    assert "derived from pyproject: v1.2.3" in out
    assert "release-preflight: PASS" in out
    assert _git(repo, "tag", "--list").stdout.strip() == ""
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""
    commands = [cmd for cmd in deps.commands]
    assert ["uv", "lock", "--check"] in commands
    assert ["make", "pin-audit"] in commands
    assert ["make", "ci-gates-parity"] in commands
    assert ["make", "docs-check"] in commands
    assert any(cmd[:3] == [sys.executable, "-m", "pytest"] for cmd in commands)
    assert not any("tag" in argument for cmd in commands for argument in cmd)


def test_targeted_release_tests_exist() -> None:
    failing = [path for path in release_preflight.TARGETED_TESTS if not (ROOT / path).is_file()]
    assert failing == [], f"targeted release tests do not resolve: {failing}"


def test_supplied_tag_must_match_the_package_version(tmp_path, capsys) -> None:
    repo = _repo(tmp_path)
    rc = _run(repo, FakeDeps(), tag="v1.2.4")
    captured = capsys.readouterr()
    assert rc == 1
    assert "FAIL tag" in captured.out
    assert "does not match pyproject version 1.2.3" in captured.out
    assert "release-preflight: FAIL" in captured.err


def test_version_mismatch_between_pyproject_and_init_fails(tmp_path, capsys) -> None:
    repo = _repo(tmp_path, init_version="1.2.2")
    rc = _run(repo, FakeDeps())
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL version" in out
    assert "pyproject.toml=1.2.3" in out
    assert "src/provisioning/__init__.py=1.2.2" in out


def test_missing_changelog_entry_fails(tmp_path, capsys) -> None:
    repo = _repo(tmp_path, changelog="## 1.2.2\n\nOld release.\n")
    rc = _run(repo, FakeDeps())
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL changelog" in out
    assert "no `## 1.2.3` heading" in out


def test_missing_changelog_file_fails(tmp_path, capsys) -> None:
    repo = _repo(tmp_path, changelog=None)
    rc = _run(repo, FakeDeps())
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL changelog" in out
    assert "CHANGELOG.md not found" in out


def test_existing_local_tag_fails(tmp_path, capsys) -> None:
    repo = _repo(tmp_path)
    rc = _run(repo, FakeDeps(local=True))
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL tag-local" in out
    assert "tag v1.2.3 already exists locally" in out


def test_existing_remote_tag_fails(tmp_path, capsys) -> None:
    repo = _repo(tmp_path)
    rc = _run(repo, FakeDeps(remote=True))
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL tag-remote" in out
    assert "tag v1.2.3 already exists on origin" in out


def test_remote_probe_failure_fails_closed(tmp_path, capsys) -> None:
    repo = _repo(tmp_path)

    def broken(root: Path, tag: str) -> bool:
        raise release_preflight.PreflightError("cannot query origin: no origin remote")

    rc = release_preflight.run_preflight(
        repo,
        runner=FakeDeps().run,
        local_tag_exists=lambda root, tag: False,
        remote_tag_exists=broken,
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL tag-remote" in out
    assert "no origin remote" in out


def test_dirty_worktree_fails(tmp_path, capsys) -> None:
    repo = _repo(tmp_path)
    (repo / "scratch.txt").write_text("untracked\n", encoding="utf-8")
    rc = _run(repo, FakeDeps())
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL worktree" in out
    assert "worktree is dirty" in out
    assert "scratch.txt" in out


def test_branch_mismatch_fails(tmp_path, capsys) -> None:
    repo = _repo(tmp_path)
    _git(repo, "branch", "-m", "trunk")
    rc = _run(repo, FakeDeps())
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL branch" in out
    assert "on `trunk`, expected `main`" in out


def test_branch_is_overridable(tmp_path, capsys) -> None:
    repo = _repo(tmp_path)
    _git(repo, "branch", "-m", "release")
    rc = _run(repo, FakeDeps(), branch="release")
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "PASS branch" in out


def test_failed_command_names_the_check_and_command(tmp_path, capsys) -> None:
    repo = _repo(tmp_path)
    deps = FakeDeps(rc=1)
    rc = _run(repo, deps)
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL lock" in out
    assert "`uv lock --check` exited 1" in out
    assert "FAIL release-tests" in out


def test_dynamic_or_missing_pyproject_version_fails_clearly(tmp_path, capsys) -> None:
    repo = _repo(tmp_path)
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "sample"\ndynamic = ["version"]\n', encoding="utf-8"
    )
    rc = _run(repo, FakeDeps())
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL version" in out
    assert "no static [project].version" in out


@pytest.mark.parametrize("tag", ["1.2.3", "v1.2", "release-1.2.3"])
def test_invalid_supplied_tag_shape_fails(tmp_path, capsys, tag: str) -> None:
    repo = _repo(tmp_path)
    rc = _run(repo, FakeDeps(), tag=tag)
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL tag" in out
    assert "not vMAJOR.MINOR.PATCH" in out
