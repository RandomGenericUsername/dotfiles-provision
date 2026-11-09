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
    assert assert_task.get("when") == "not ansible_check_mode", (
        "the config precondition must stay check-gated so a standalone "
        "--check (without runtime-daemon) remains dry"
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


def test_seed_captures_the_generation_and_asserts_v3_postconditions() -> None:
    """Generations v3: rc=0 is success even on an idempotent no-op seed; a
    tolerated rc=1 must still commit fresh state; the committed manifest's
    generationHash must be the current target basename. v2 consumer links under
    the install spine are not part of the seed."""
    play = _play()
    names = _task_names(play)
    assert "Capture the generation manifest before seeding" in names
    assert "Capture the generation manifest after seeding" in names
    after = names.index("Capture the generation manifest after seeding")
    assert after < names.index("Assert the seed produced acceptable generation state")
    assert names.index("Assert the seed produced acceptable generation state") < names.index(
        "Assert the seed committed one complete v3 generation"
    )
    assert str(play["vars"]["runtime_seed_current_dir"]) == (
        "{{ runtime_seed_state_home | trim }}/dotfiles/current"
    )
    assert str(play["vars"]["runtime_seed_generation_manifest"]) == (
        "{{ runtime_seed_current_dir }}/manifest.json"
    )
    assert "runtime_seed_consumer_links" not in play["vars"]

    accepted = next(
        task
        for task in play["tasks"]
        if str(task.get("name")) == "Assert the seed produced acceptable generation state"
    )
    that = " ".join(str(item) for item in accepted["ansible.builtin.assert"]["that"])
    assert "runtime_seed_result.rc in [0, 1]" in that
    # rc=0 accepts an unchanged (idempotent) committed manifest; only rc=1
    # requires state advancement (BUG-006).
    assert "runtime_seed_result.rc == 0 or runtime_seed_state_advanced | bool" in that
    assert "runtime_seed_post_state.stat.exists" in that

    generation = next(
        task
        for task in play["tasks"]
        if str(task.get("name")) == "Assert the seed committed one complete v3 generation"
    )
    that = " ".join(str(item) for item in generation["ansible.builtin.assert"]["that"])
    assert "runtime_seed_generation.version == 3" in that
    assert "generationHash is match" in that
    assert "runtime_seed_current_link.stdout | trim | basename" in that
    assert "appearance.tokensPath == 'appearance/tokens.json'" in that
    assert "appearance.targets | length > 0" in that
    assert "generations.md v0.9.0" in str(
        generation["ansible.builtin.assert"]["fail_msg"]
    )



_GENERATION_SCRIPT = r"""#!/usr/bin/env python3
import json
import pathlib
import sys

state = pathlib.Path(sys.argv[1])
gen_hash = "a" * 64
gen = state / "dotfiles" / "generations" / gen_hash
(gen / "appearance").mkdir(parents=True, exist_ok=True)
(gen / "appearance" / "tokens.json").write_text("{}\n", encoding="utf-8")
(gen / "appearance" / "ags.css").write_text("/* seed */\n", encoding="utf-8")
manifest = {
    "version": 3,
    "generationHash": gen_hash,
    "created": {"at": "2026-11-06T00:00:00Z"},
    "committed": {"at": "2026-11-06T00:00:01Z"},
    "layers": {
        "wallpaper": {"entryHash": "b" * 64, "path": "wallpaper"},
        "palette": {"entryHash": "c" * 64, "path": "palette"},
    },
    "skin": {"name": "glass", "entryHash": "d" * 64, "mode": "dark"},
    "appearance": {
        "tokensPath": "appearance/tokens.json",
        "targets": [{"configDir": "ags", "path": "appearance/ags.css"}],
    },
    "mode": "dark",
    "intent": {
        "wallpaper": "b" * 64,
        "palette": "c" * 64,
        "skin": "glass",
        "mode": "dark",
    },
    "source": {"kind": "cli", "intentHash": "e" * 64},
}
(gen / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")
current = state / "dotfiles" / "current"
tmp = state / "dotfiles" / "current.tmp"
if tmp.is_symlink() or tmp.exists():
    tmp.unlink()
tmp.symlink_to(pathlib.Path("generations") / gen_hash)
tmp.replace(current)
"""

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
        fake_generation = bin_dir / "fake-generation.py"
        fake_generation.write_text(_GENERATION_SCRIPT, encoding="utf-8")
        fake_generation.chmod(0o755)
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

    def test_seed_resolves_tpr_from_config_despite_stale_env(self) -> None:
        """BUG-008: the seed must resolve tpr from the spine producer config. If
        the old single/double-underscore ambient env were authoritative, the
        stale value below would silently select it."""
        import shutil
        import tempfile

        if shutil.which("ansible-playbook") is None:
            pytest.skip("ansible-playbook not installed")
        with tempfile.TemporaryDirectory() as raw:
            env, bin_dir, state, install = self._env(Path(raw))
            env["RUNTIME_PALETTE_PRODUCER"] = "stale"
            env["RUNTIME__PALETTE__PRODUCER"] = "stale"
            env["RUNTIME__PALETTE__TPR_ENGINE"] = "matugen"
            marker = Path(raw) / "resolved-producer.txt"
            config = install / "config" / "dotfiles-runtime" / "producer.json"
            stub = bin_dir / "dotfiles-runtime"
            stub.write_text(
                "#!/bin/sh\n"
                "set -eu\n"
                f"producer=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[\"producer\"])' {config})\n"
                "printf '%s %s %s\\n' \"$producer\" \"${RUNTIME_PALETTE_PRODUCER:-}\" \"${RUNTIME__PALETTE__PRODUCER:-}\" > "  # noqa: E501
                f"{marker}\n"
                f"python3 {bin_dir}/fake-generation.py {state}\n"
                "exit 0\n"
            )
            stub.chmod(0o755)

            result = self._run(env, install)
            assert result.returncode == 0, result.stdout + result.stderr
            assert marker.read_text().strip() == "tpr stale stale", (
                "the seed must resolve producer=tpr from producer.json even "
                "with stale single/double-underscore ambient env present; got "
                + marker.read_text()
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
            assert "current/manifest.json" in result.stdout + result.stderr, (
                "the failure must name the missing generation manifest; output:\n"
                + result.stdout
                + result.stderr
            )

    def test_rc0_with_an_unchanged_valid_manifest_is_accepted(self) -> None:
        """An idempotent apply derives the same generation: rc=0 without any
        manifest change is success, not a missing fresh generation."""
        import shutil
        import tempfile

        if shutil.which("ansible-playbook") is None:
            pytest.skip("ansible-playbook not installed")
        with tempfile.TemporaryDirectory() as raw:
            env, bin_dir, state, install = self._env(Path(raw))
            subprocess.run(
                ["python3", str(bin_dir / "fake-generation.py"), str(state)],
                check=True,
            )
            stub = bin_dir / "dotfiles-runtime"
            stub.write_text("#!/bin/sh\nexit 0\n")
            stub.chmod(0o755)

            result = self._run(env, install)
            assert result.returncode == 0, result.stdout + result.stderr
            assert "Assert the seed produced acceptable generation state" in result.stdout

    def test_rc_greater_than_one_fails(self) -> None:
        import shutil
        import tempfile

        if shutil.which("ansible-playbook") is None:
            pytest.skip("ansible-playbook not installed")
        with tempfile.TemporaryDirectory() as raw:
            env, bin_dir, state, install = self._env(Path(raw))
            subprocess.run(
                ["python3", str(bin_dir / "fake-generation.py"), str(state)],
                check=True,
            )
            stub = bin_dir / "dotfiles-runtime"
            stub.write_text("#!/bin/sh\necho 'hard seed failure' >&2\nexit 2\n")
            stub.chmod(0o755)

            result = self._run(env, install)
            assert result.returncode != 0, result.stdout + result.stderr
            assert "hard seed failure" in result.stdout + result.stderr

    def test_rc1_with_fresh_state_and_complete_links_is_accepted(self) -> None:
        import shutil
        import tempfile

        if shutil.which("ansible-playbook") is None:
            import pytest

            pytest.skip("ansible-playbook not installed")
        with tempfile.TemporaryDirectory() as raw:
            env, bin_dir, state, install = self._env(Path(raw))
            stub = bin_dir / "dotfiles-runtime"
            stub.write_text(
                "#!/bin/sh\n"
                f"python3 {bin_dir}/fake-generation.py {state}\n"
                "echo 'transient reload failure' >&2\n"
                "exit 1\n"
            )
            stub.chmod(0o755)

            result = self._run(env, install)
            assert result.returncode == 0, result.stdout + result.stderr
