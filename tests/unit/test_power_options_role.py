"""REQ-003: keep Bluetooth available in the power-options profiles.

The role rewrites `block_bt = true` to `false` in Powersave/Powersave++/
Balanced, refreshes the active profile, and verify reads the deployed files.
Tests are pure YAML; no Ansible run and no host mutation.
"""

from __future__ import annotations

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ROLE = _REPO_ROOT / "ansible" / "roles" / "power_options"
_VERIFY_VARS = _REPO_ROOT / "ansible" / "roles" / "verify" / "vars" / "main.yml"
_VERIFY_TASKS = _REPO_ROOT / "ansible" / "roles" / "verify" / "tasks" / "main.yml"
_PLAYBOOK = _REPO_ROOT / "ansible" / "playbooks" / "power-options.yaml"
_EXPECTED = ["Powersave++.toml", "Powersave.toml", "Balanced.toml"]


def _role_vars() -> dict:
    return yaml.safe_load((_ROLE / "vars" / "main.yml").read_text())


def _role_tasks() -> list[dict]:
    data = yaml.safe_load((_ROLE / "tasks" / "main.yml").read_text())
    assert isinstance(data, list)
    return data


def test_role_targets_the_three_blocking_profiles() -> None:
    data = _role_vars()
    assert data["power_options_profile_dir"] == "/etc/power-options/profiles"
    assert data["power_options_marker"] == "/etc/power-options/.dotfiles-bt-ok"
    assert [str(p) for p in data["power_options_bt_profiles"]] == _EXPECTED


def test_role_flips_block_bt_and_is_become_scoped() -> None:
    tasks = _role_tasks()
    replace = next(
        task for task in tasks if task.get("name") == "Disable Bluetooth soft-blocking in the power profiles"
    )
    module = replace["ansible.builtin.replace"]
    assert module["regexp"] == "^block_bt = true$"
    assert module["replace"] == "block_bt = false"
    assert str(replace["loop"]) == "{{ power_options_bt_profiles }}"

    play = yaml.safe_load(_PLAYBOOK.read_text())[0]
    assert play["become"] is True
    assert play["roles"] == ["power_options"]


def test_role_refreshes_only_when_a_profile_changed() -> None:
    tasks = _role_tasks()
    refresh = next(
        task for task in tasks if task.get("name") == "Refresh the active power profile after changing the Bluetooth setting"
    )
    restart = next(
        task for task in tasks if task.get("name") == "Restart power-options to reload the edited profiles"
    )
    assert restart["ansible.builtin.systemd_service"] == {
        "name": "power-options.service",
        "state": "restarted",
    }
    joined = " ".join(restart["when"])
    assert "power_options_profile_dir_stat.stat.isdir | default(false)" in joined
    assert "power_options_bt_replace.changed | default(false)" in joined
    assert "power_options_marker_write.changed | default(false)" in joined
    assert refresh["ansible.builtin.command"]["argv"] == ["power-daemon-mgr", "refresh-full"]
    when = refresh["when"]
    assert "power_options_bt_replace.changed | default(false)" in " ".join(when)


def test_verify_reads_the_same_profiles() -> None:
    vars_data = yaml.safe_load(_VERIFY_VARS.read_text())
    assert [str(p) for p in vars_data["verify_power_options_bt_profiles"]] == _EXPECTED
    assert vars_data["verify_power_options_marker"] == "/etc/power-options/.dotfiles-bt-ok"
    tasks = yaml.safe_load(_VERIFY_TASKS.read_text())
    names = [str(task.get("name", "")) for task in tasks]
    assert "Check the power-options Bluetooth policy marker" in names
    assert "Read the power-options Bluetooth profiles" in names
    assert "Assert the power-options profiles do not soft-block Bluetooth" in names

def test_role_writes_the_policy_marker() -> None:
    tasks = _role_tasks()
    marker = next(
        task for task in tasks if task.get("name") == "Record that the Bluetooth profile policy is applied"
    )
    assert marker["ansible.builtin.copy"]["dest"] == "{{ power_options_marker }}"
    assert marker["ansible.builtin.copy"]["content"] == "{{ power_options_marker_content }}"
    assert "policy_version = 2" in _role_vars()["power_options_marker_content"]
