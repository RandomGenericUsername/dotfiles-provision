"""Structural tests for the reduced gui_tools role (REQ-008 final topology).

The AGS app lifecycle moved to `ags_apps_units` (the only installer). gui_tools
now owns only the two independent desktop prerequisites: dunst stop/mask (so
the notification overlay can own org.freedesktop.Notifications) and the
inode/directory handler pin.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_TASK_KEYWORDS = {
    "name",
    "when",
    "become",
    "become_user",
    "become_method",
    "become_flags",
    "args",
    "register",
    "changed_when",
    "failed_when",
    "creates",
    "vars",
    "loop",
    "loop_control",
    "until",
    "retries",
    "delay",
    "tags",
    "environment",
    "ignore_errors",
    "notify",
    "block",
    "rescue",
    "always",
    "check_mode",
}


def _find_ansible_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "ansible" / "inventory" / "localhost.yaml"
        if candidate.is_file() and (parent / "pyproject.toml").is_file():
            return parent / "ansible"
    raise FileNotFoundError("ansible/ not found walking up from the test file")


_ANSIBLE_DIR = _find_ansible_dir()
_ROLE = _ANSIBLE_DIR / "roles" / "gui_tools"


def _module_key(task: dict[str, Any]) -> str | None:
    for key in task:
        if key not in _TASK_KEYWORDS:
            return key
    return None


def _tasks() -> list[dict[str, Any]]:
    return [dict(item) for item in yaml.safe_load((_ROLE / "tasks" / "main.yml").read_text())]


def _vars() -> dict[str, Any]:
    return dict(yaml.safe_load((_ROLE / "vars" / "main.yml").read_text()))


class TestRoleTree:
    def test_role_tree_exists(self) -> None:
        assert (_ROLE / "tasks" / "main.yml").is_file()
        assert (_ROLE / "vars" / "main.yml").is_file()


class TestNoAgsOwnership:
    def test_no_ags_instance_lifecycle_remains(self) -> None:
        text = (_ROLE / "tasks" / "main.yml").read_text()
        assert "ags quit" not in text
        assert "ags list" not in text
        assert "ags run" not in text
        assert "gui_tools_ags_instances" not in text
        variables = (_ROLE / "vars" / "main.yml").read_text()
        assert "gui_tools_ags_instances" not in variables
        assert "gui_tools_ags_always_on" not in variables

    def test_no_app_placement_or_composition_read(self) -> None:
        text = (_ROLE / "tasks" / "main.yml").read_text()
        assert "apps.yaml" not in text
        assert "manifests_dir" not in text
        assert "gui_tools_config_dirs" not in text
        assert "gui_tools_app_files" not in text

    def test_no_per_file_capture_or_selector_manifests(self) -> None:
        variables = _vars()
        for retired in (
            "gui_tools_app_files",
            "gui_tools_capture_obsolete",
            "gui_tools_icme_app_files",
            "gui_tools_wallpaper_selector_app_files",
            "gui_tools_notifications_app_files",
            "gui_tools_btop_studio_app_files",
        ):
            assert retired not in variables, retired


class TestDunstAndDirectoryHandler:
    def test_dunst_is_stopped_and_masked(self) -> None:
        commands = [
            str(task.get(_module_key(task) or "", ""))
            for task in _tasks()
            if _module_key(task) == "ansible.builtin.command"
        ]
        assert any("disable --now dunst.service" in command for command in commands)
        assert any("mask dunst.service" in command for command in commands)
        assert _vars()["gui_tools_masked_user_units"] == ["dunst.service"]

    def test_dunst_tasks_are_check_gated_and_non_fatal(self) -> None:
        for task in _tasks():
            command = str(task.get(_module_key(task) or "", ""))
            if "dunst.service" in command:
                assert task.get("when") == "not ansible_check_mode"
                assert task.get("failed_when") is False
                assert task.get("changed_when") is False

    def test_directory_handler_is_pinned_to_thunar(self) -> None:
        commands = [
            str(task.get(_module_key(task) or "", ""))
            for task in _tasks()
            if _module_key(task) == "ansible.builtin.command"
        ]
        assert any(
            "xdg-mime default thunar.desktop inode/directory" in command
            for command in commands
        )

    def test_no_become_anywhere(self) -> None:
        for task in _tasks():
            assert "become" not in task
            assert "become_user" not in task
