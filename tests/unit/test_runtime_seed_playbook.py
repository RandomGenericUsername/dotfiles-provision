"""BUG-001: the seed step runs the installed pinned runtime, not a source tree.

`runtime-seed.yaml` used to build the runtime from the composition checkout,
which no longer exists after REQ-002. The seed must spawn the binary `cli_tools`
installed into the uv tool bin dir, exactly like the systemd units.
"""

from __future__ import annotations

from pathlib import Path

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
