"""BUG-001: the seed step runs the installed pinned runtime, not a source tree.

`runtime-seed.yaml` used to build the runtime from the composition checkout,
which no longer exists after REQ-002. The seed must spawn the binary `cli_tools`
installed into the uv tool bin dir, exactly like the systemd units.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PLAYBOOK = _REPO_ROOT / "ansible" / "playbooks" / "runtime-seed.yaml"


def _play() -> dict:
    data = yaml.safe_load(_PLAYBOOK.read_text(encoding="utf-8"))
    assert isinstance(data, list) and len(data) == 1
    return data[0]


def _seed_task(play: dict) -> dict:
    matches = [
        task
        for task in play["tasks"]
        if "Seed runtime state" in str(task.get("name", ""))
    ]
    assert len(matches) == 1, "expected exactly one seed task"
    return matches[0]


def test_seed_runs_the_installed_dotfiles_runtime() -> None:
    play = _play()
    task = _seed_task(play)
    argv = task["ansible.builtin.command"]["argv"]
    assert argv[0] == "{{ runtime_seed_bin_dir | trim }}/dotfiles-runtime"
    assert argv[1:3] == ["wallpaper", "set"]
    assert argv[3] == "{{ install_dir | trim }}/wallpapers/default.png"

    bin_dir = str(play["vars"]["runtime_seed_bin_dir"])
    assert "UV_TOOL_BIN_DIR" in bin_dir
    assert "XDG_BIN_HOME" in bin_dir
    assert ".local/bin" in bin_dir


def test_seed_has_no_composition_source_path() -> None:
    text = _PLAYBOOK.read_text(encoding="utf-8")
    assert "src/runtime" not in text
    assert "uv run --directory" not in text
    assert "composition_root" not in text


def test_seed_stays_check_gated() -> None:
    task = _seed_task(_play())
    assert task.get("when") == "not ansible_check_mode"
    assert task.get("changed_when") == "runtime_seed_result.rc == 0"
    assert task.get("failed_when") == "runtime_seed_result.rc not in [0, 1]"


def test_seed_requires_the_runtime_producer_config() -> None:
    """BUG-007/BUG-008: the runtime reads the spine producer config, not ambient
    env. runtime_daemon renders it before this playbook; the seed asserts it."""
    play = _play()
    assert str(play["vars"]["runtime_seed_producer_config"]) == (
        "{{ install_dir | trim }}/config/dotfiles-runtime/producer.json"
    )
    tasks = play["tasks"]
    stat = next(t for t in tasks if str(t.get("name")) == "Check the runtime producer config exists before seeding")
    assert stat["ansible.builtin.stat"]["path"] == "{{ runtime_seed_producer_config }}"
    assert_task = next(t for t in tasks if str(t.get("name")) == "Assert the runtime producer config exists before seeding")
    assert "runtime_seed_producer_config_check.stat.isreg" in str(
        assert_task["ansible.builtin.assert"]["that"]
    )
    names = [str(t.get("name", "")) for t in tasks]
    assert names.index(stat["name"]) < names.index("Seed runtime state from default wallpaper")


def test_seed_never_injects_producer_environment() -> None:
    """A stale single/double-underscore env must not select the seed producer:
    the runtime resolves the spine config instead."""
    text = _PLAYBOOK.read_text(encoding="utf-8")
    assert "RUNTIME__PALETTE" not in text
    assert "RUNTIME_PALETTE" not in text
    assert "environment:" not in text


def _task_names(play: dict) -> list[str]:
    return [str(task.get("name", "")) for task in play["tasks"]]


def test_seed_captures_pre_state_and_asserts_postconditions() -> None:
    """BUG-006: a tolerated rc=1 must still produce fresh current.json and
    every consumer link, otherwise the bootstrap fails."""
    play = _play()
    names = _task_names(play)
    assert "Capture the runtime state before seeding" in names
    assert "Capture the runtime state after seeding" in names
    after = names.index("Capture the runtime state after seeding")
    assert after < names.index("Assert runtime seed produced fresh state and complete consumer links")
    assert str(play["vars"]["runtime_seed_current_state"]) == (
        "{{ runtime_seed_state_home | trim }}/dotfiles/current.json"
    )
    links = [str(link) for link in play["vars"]["runtime_seed_consumer_links"]]
    for name in ("ags/colors.css", "gtk-3.0/colors.css", "gtk-4.0/colors.css", "rofi/colors.rasi", "btop/themes/colors.btop.theme"):
        assert any(name in link for link in links), f"missing consumer link {name}"

    assert_task = next(
        task
        for task in play["tasks"]
        if str(task.get("name")) == "Assert runtime seed produced fresh state and complete consumer links"
    )
    that = " ".join(str(item) for item in assert_task["ansible.builtin.assert"]["that"])
    assert "runtime_seed_result.rc in [0, 1]" in that
    assert "runtime_seed_state_advanced | bool" in that
    assert "selectattr('stat.islnk')" in that
    assert "dotfiles/current" in that
    assert "selectattr('stat.exists')" in that
    assert "missing_or_unresolved" in str(assert_task["ansible.builtin.assert"]["fail_msg"])


@pytest.mark.integration
class TestSeedPostconditionsExecution:
    """Run the real runtime-seed playbook against a stubbed runtime binary:
    rc alone is not enough (BUG-006 negative/positive lock)."""

    def _env(self, tmp: Path) -> tuple[dict[str, str], Path, Path, Path]:
        import os

        home = tmp / "home"
        xdg_state = tmp / "state"
        bin_dir = tmp / "bin"
        install = tmp / "install"
        for path in (home, xdg_state, bin_dir, install / "config" / "dotfiles-runtime", install / "wallpapers"):
            path.mkdir(parents=True, exist_ok=True)
        (install / "config" / "dotfiles-runtime" / "producer.json").write_text(
            '{"schema_version":1,"producer":"tpr","tpr_engine":"native","tpr_runtime":"container"}\n'
        )
        (install / "wallpapers" / "default.png").write_bytes(b"\x89PNG")
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("ANSIBLE_", "XDG_", "UV_TOOL_"))
        }
        env.update(
            HOME=str(home),
            XDG_STATE_HOME=str(xdg_state),
            XDG_BIN_HOME=str(bin_dir),
            ANSIBLE_CONFIG=str(_REPO_ROOT / "ansible" / "ansible.cfg"),
        )
        return env, bin_dir, xdg_state, install

    def _run(self, env: dict[str, str], install: Path) -> subprocess.CompletedProcess[str]:
        import shutil
        import subprocess

        return subprocess.run(
            [
                shutil.which("ansible-playbook"),
                str(_PLAYBOOK),
                "-e",
                f"install_dir={install}",
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=180,
        )

    def test_rc1_without_fresh_state_or_links_fails_with_the_missing_path(self) -> None:
        import shutil
        import tempfile

        if shutil.which("ansible-playbook") is None:
            import pytest

            pytest.skip("ansible-playbook not installed")
        with tempfile.TemporaryDirectory() as raw:
            env, bin_dir, _state, install = self._env(Path(raw))
            stub = bin_dir / "dotfiles-runtime"
            stub.write_text("#!/bin/sh\necho 'simulated transient seed failure' >&2\nexit 1\n")
            stub.chmod(0o755)

            result = self._run(env, install)
            assert result.returncode != 0, result.stdout + result.stderr
            assert "rofi/colors.rasi" in result.stdout + result.stderr, (
                "the failure must name the missing consumer path; output:\n"
                + result.stdout
                + result.stderr
            )

    def test_rc1_with_fresh_state_and_complete_links_is_accepted(self) -> None:
        import shutil
        import tempfile

        if shutil.which("ansible-playbook") is None:
            import pytest

            pytest.skip("ansible-playbook not installed")
        with tempfile.TemporaryDirectory() as raw:
            env, bin_dir, state, install = self._env(Path(raw))
            current = state / "dotfiles" / "current"
            current.mkdir(parents=True)
            (state / "dotfiles" / "current.json").write_text('{"schema_version": 2}\n')
            artifacts = {
                "config/ags/colors.css": "colors.gtk.css",
                "config/gtk-3.0/colors.css": "colors.gtk.css",
                "config/gtk-4.0/colors.css": "colors.adw.css",
                "config/rofi/colors.rasi": "colors.rasi",
                "config/btop/themes/colors.btop.theme": "colors.btop.theme",
            }
            for artifact in artifacts.values():
                (current / artifact).write_text("x\n")
            for link, artifact in artifacts.items():
                target = install / link
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(current / artifact)
            stub = bin_dir / "dotfiles-runtime"
            stub.write_text(
                "#!/bin/sh\n"
                f"printf '%s\\n' '{{\"schema_version\": 2, \"advanced\": true}}' > {state}/dotfiles/current.json\n"
                "echo 'transient reload failure' >&2\n"
                "exit 1\n"
            )
            stub.chmod(0o755)

            result = self._run(env, install)
            assert result.returncode == 0, result.stdout + result.stderr
