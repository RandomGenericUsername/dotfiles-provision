"""REQ-008: the final all-standalone AGS install topology.

`ags_apps_units` is the ONLY AGS app installer. These tests pin the structure
(one owner per app, immutable tags, the shared platform shortcut,
quiesce->repoint->start->verify ordering, rollback, launch lock, launcher
toggle/request behavior, autostart identities) and execute the role against
seven local fake app repos with a fake AGS CLI — GUI-free, no network.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
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
    "delegate_to",
    "run_once",
}


def _find_ansible_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "ansible" / "inventory" / "localhost.yaml"
        if candidate.is_file() and (parent / "pyproject.toml").is_file():
            return parent / "ansible"
    raise FileNotFoundError("ansible/ not found walking up from the test file")


_ANSIBLE_DIR = _find_ansible_dir()
_ENGINE_ROOT = _ANSIBLE_DIR.parent
_ROLES_DIR = _ANSIBLE_DIR / "roles"
_ROLE = _ROLES_DIR / "ags_apps_units"
_FIXTURES = _ENGINE_ROOT / "tests" / "fixtures" / "ags-apps"
_APP_LISTS = _FIXTURES / "app-list"
_FAKE_APP = _FIXTURES / "fake-app"
_ASSETS_AUTOSTART = _FIXTURES / "autostart" / "v0.12.1.lua"

_SEVEN_APPS = [
    "bar",
    "notifications",
    "capture",
    "clipboard",
    "wallpaper-selector",
    "icme",
    "btop-theme-studio",
]

#: The released tags of the final all-standalone epoch (REQ-030).
_FINAL_APP_TAGS = {
    "bar": "v0.6.0",
    "notifications": "v0.5.0",
    "capture": "v0.7.0",
    "clipboard": "v0.6.0",
    "wallpaper-selector": "v0.5.0",
    "icme": "v0.5.0",
    "btop-theme-studio": "v0.5.0",
}


def _tasks_file(name: str = "main.yml") -> list[dict[str, Any]]:
    data = yaml.safe_load((_ROLE / "tasks" / name).read_text())
    assert isinstance(data, list), f"{name} must be a task list"
    return [dict(item) for item in data]


def _all_tasks() -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for path in sorted((_ROLE / "tasks").glob("*.yml")):
        data = yaml.safe_load(path.read_text())
        assert isinstance(data, list)
        tasks.extend(dict(item) for item in data)
    return tasks


def _module_key(task: dict[str, Any]) -> str | None:
    for key in task:
        if key not in _TASK_KEYWORDS:
            return key
    return None


def _module(task: dict[str, Any]) -> dict[str, Any]:
    module = task.get(_module_key(task) or "", {})
    if isinstance(module, str):
        return {"_raw": module}
    assert isinstance(module, dict)
    return dict(module)


def _app_list(name: str = "all-standalone.apps.yaml") -> list[dict[str, Any]]:
    data = yaml.safe_load((_APP_LISTS / name).read_text())
    assert isinstance(data, dict)
    return list(data["apps"])


class TestAllStandaloneFixture:
    def test_fixture_declares_the_seven_final_apps(self) -> None:
        apps = _app_list()
        assert [entry["app"] for entry in apps] == _SEVEN_APPS
        assert {entry["owner"] for entry in apps} == {"standalone"}

    def test_fixture_pins_the_final_released_tags(self) -> None:
        """REQ-030: the final inventory is exactly the released v3 generation.

        `dotfiles-v3` deploy-coverage compares the composition to this fixture;
        a stale tag here makes the composition/engine final topology disagree.
        """
        inventory = {entry["app"]: entry["tag"] for entry in _app_list()}
        assert inventory == _FINAL_APP_TAGS

    def test_every_app_has_exactly_one_owner_and_unique_surfaces(self) -> None:
        apps = _app_list()
        for field in (
            "app",
            "installDir",
            "instance",
            "configDir",
            "configLink",
            "spineLink",
            "xdgLink",
        ):
            values = [entry[field] for entry in apps]
            assert len(values) == len(set(values)), f"{field} must be unique"

    def test_only_the_bar_owns_the_palette_pointer(self) -> None:
        pointers = [entry["app"] for entry in _app_list() if entry.get("barPalettePointer")]
        assert pointers == ["bar"]

    def test_always_on_and_on_demand_split_matches_the_session(self) -> None:
        apps = {entry["app"]: entry for entry in _app_list()}
        assert apps["bar"]["launch"] == "always"
        assert apps["notifications"]["launch"] == "always"
        for app in ("capture", "clipboard", "wallpaper-selector", "icme", "btop-theme-studio"):
            assert apps[app]["launch"] == "on-demand"

    def test_launcher_and_autostart_surfaces_cover_the_keybinds_and_login(self) -> None:
        apps = {entry["app"]: entry for entry in _app_list()}
        assert apps["capture"]["launcher"] == "capture-ui"
        assert apps["capture"]["binLink"] == "capture-tool"
        assert apps["clipboard"]["launcher"] == "clipboard-ui"
        assert apps["wallpaper-selector"]["launcher"] == "wallpaper-selector-ui"
        assert apps["icme"]["launcher"] == "icon-color-mapping-editor"
        assert apps["btop-theme-studio"]["launcher"] == "btop-theme-studio"
        assert "launcher" not in apps["bar"]
        assert "launcher" not in apps["notifications"]

        # The app list still records the autostart identity for the always-on
        # pair (the unit template/handoff uses it), but assets v0.12.1 removed
        # those lines: only the boot-staggered on-demand capture and clipboard
        # overlays launch at login. The selector/icme/studio have no identity.
        assert apps["bar"]["autostart"] == "ags"
        assert apps["notifications"]["autostart"] == "notifications"
        assert apps["capture"]["autostart"] == "capture"
        assert apps["clipboard"]["autostart"] == "clipboard"
        for app in ("wallpaper-selector", "icme", "btop-theme-studio"):
            assert "autostart" not in apps[app]

    def test_assets_v0121_autostart_owns_only_on_demand_launches(self) -> None:
        content = _ASSETS_AUTOSTART.read_text()
        for entry in _app_list():
            identity = entry["autostart"] if "autostart" in entry else entry["instance"]
            occurrences = content.count(f"--expect-instance {identity}")
            if entry["launch"] == "always":
                assert occurrences == 0, (
                    f"{entry['app']} is unit-owned and must not be autostarted"
                )
            elif "autostart" in entry:
                assert occurrences == 1, identity
                assert "ags-run-locked" in content
            else:
                assert occurrences == 0, identity


class TestRoleStructure:
    def test_role_and_playbook_exist(self) -> None:
        assert (_ROLE / "tasks" / "main.yml").is_file()
        assert (_ROLE / "vars" / "main.yml").is_file()
        assert (_ANSIBLE_DIR / "playbooks" / "ags-apps-units.yaml").is_file()

    def test_legacy_monorepo_role_and_playbook_are_retired(self) -> None:
        assert not (_ROLES_DIR / "ags_apps").exists()
        assert not (_ANSIBLE_DIR / "playbooks" / "ags-apps.yaml").exists()
        imports = [
            str(entry["import_playbook"])
            for entry in yaml.safe_load((_ANSIBLE_DIR / "playbooks" / "bootstrap.yaml").read_text())
        ]
        assert "ags-apps.yaml" not in imports
        assert "ags-apps-units.yaml" in imports

    def test_bootstrap_order_puts_gui_tools_before_the_installer(self) -> None:
        imports = [
            str(entry["import_playbook"])
            for entry in yaml.safe_load((_ANSIBLE_DIR / "playbooks" / "bootstrap.yaml").read_text())
        ]
        assert imports.index("ags-platform.yaml") < imports.index("gui-tools.yaml")
        assert imports.index("gui-tools.yaml") < imports.index("ags-apps-units.yaml")
        assert imports.index("compositor-configs.yaml") < imports.index("ags-apps-units.yaml")

    def test_install_path_and_shared_shortcut_match_ad31(self) -> None:
        vars_text = (_ROLE / "vars" / "main.yml").read_text()
        assert "install_dir | trim }}/apps" in vars_text
        assert "app.installDir" in vars_text
        assert "app.tag" in vars_text
        assert "node_modules" in vars_text
        assert "ags_apps_units_platform_shortcut" in vars_text
        assert "ags_apps_units_tuple['ags-platform']" in vars_text

    def test_role_consumes_the_program_tuple_not_a_second_pin(self) -> None:
        vars_text = (_ROLE / "vars" / "main.yml").read_text()
        assert "program-tuple.yaml" in vars_text
        assert "ags_apps_units_tuple['ags-platform']" in vars_text
        assert "v1.0.0" not in vars_text
        assert "ags_apps_version" not in vars_text

    def test_main_task_asserts_every_entry_is_standalone(self) -> None:
        text = (_ROLE / "tasks" / "main.yml").read_text()
        assert "difference(['standalone'])" in text
        assert "owner', 'equalto', 'legacy'" not in text
        assert "is dormant" not in text

    def test_quiesce_happens_before_install_and_links(self) -> None:
        one = _tasks_file("_one.yml")
        names: list[str] = []

        def collect(items: list[dict[str, Any]]) -> None:
            for item in items:
                names.append(str(item.get("name", "")))
                if isinstance(item.get("block"), list):
                    collect(item["block"])

        collect(one)
        quiesce_index = next(
            i for i, n in enumerate(names) if "quiesce before any link change" in n
        )
        clone_index = next(i for i, n in enumerate(names) if "clone the standalone tag" in n)
        spine_index = next(i for i, n in enumerate(names) if "repoint the spine link" in n)
        assert quiesce_index < clone_index < spine_index

    def test_cutover_has_rollback_rescue(self) -> None:
        block_task = next(
            item for item in _tasks_file("_one.yml") if "block" in item and "rescue" in item
        )
        rescue = block_task["rescue"]
        assert any(
            "ROLLBACK" in str(step.get("name", "")) for step in rescue if isinstance(step, dict)
        )
        rollback = (_ROLE / "tasks" / "_rollback.yml").read_text()
        assert "previous_spine_target" in rollback
        assert "previous_xdg_target" in rollback
        assert "was_running" in rollback
        assert "ags_apps_units_run_locked" in rollback

    def test_no_role_task_writes_inside_the_immutable_tag(self) -> None:
        forbidden = {
            "ansible.builtin.copy",
            "ansible.builtin.template",
            "ansible.builtin.lineinfile",
            "ansible.builtin.blockinfile",
        }
        for task in _all_tasks():
            key = _module_key(task)
            module = _module(task)
            dest = str(module.get("dest", module.get("path", "")))
            if key in forbidden:
                assert "ags_apps_units_unit_dir" not in dest, (
                    f"task {task.get('name')!r} writes inside the immutable tag"
                )
            if key == "ansible.builtin.file":
                if "ags_apps_units_unit_dir" in dest:
                    allowed_delete = dest.endswith(".git") or any(
                        name in dest for name in (
                            "appearance.css",
                            "skin.css",
                            "skin.json",
                            "tokens.json",
                            "colors.",
                        )
                    )
                    assert module.get("state") == "absent" and allowed_delete, (
                        f"task {task.get('name')!r} mutates the immutable tag"
                    )

    def test_runtime_artifacts_are_swept_and_icons_are_verified(self) -> None:
        sweep = (_ROLE / "tasks" / "_one.yml").read_text()
        assert "ags_apps_units_forbidden_runtime_artifacts" in sweep
        assert "assert the tag carries no runtime artifact" in sweep
        assert "find any remaining runtime artifact" in sweep
        # Historical tags are swept too, from the same documented allowlist.
        historical = (_ROLE / "tasks" / "_sweep_tags.yml").read_text()
        assert "ags_apps_units_installed_tag_dirs" in historical
        assert "ags_apps_units_forbidden_runtime_artifacts" in historical
        assert "depth: 2" in historical
        assert "state: absent" in historical
        main = (_ROLE / "tasks" / "main.yml").read_text()
        assert "include_tasks: _sweep_tags.yml" in main
        verify_unit = (_ROLE / "tasks" / "_verify_unit.yml").read_text()
        assert "colors.css" not in verify_unit
        assert "icons.json" in verify_unit
        assert "checksum" in verify_unit
        assert "ansible.builtin.copy" not in verify_unit
        assert "ansible.builtin.template" not in verify_unit

    def test_installer_splits_the_autostart_surface_by_launch_policy(self) -> None:
        surfaces = (_ROLE / "tasks" / "_verify_surfaces.yml").read_text()
        assert "app.autostart" in surfaces
        assert "--expect-instance " in surfaces
        assert "ags-run-locked" in surfaces
        # launch: always -> unit-owned, zero autostart lines, enabled unit.
        assert "app.launch == 'always'" in surfaces
        assert "| length - 1) == 0" in surfaces, (
            "an always-on app must not be launched by autostart"
        )
        unit_check = (_ROLE / "tasks" / "_verify_always_on_unit.yml").read_text()
        assert "ags_apps_units_unit_file" in unit_check
        assert "ags_apps_units_unit_wants_link" in unit_check
        assert "isreg" in unit_check and "islnk" in unit_check
        assert "_verify_always_on_unit.yml" in (_ROLE / "tasks" / "_one.yml").read_text()
        # launch: on-demand -> exactly one locked autostart line.
        assert "app.launch == 'on-demand'" in surfaces
        assert "| length - 1) == 1" in surfaces, (
            "an on-demand autostart identity must appear exactly once "
            "(no duplicate process)"
        )


class TestSingleOwnerSurfaces:
    def test_cli_tools_no_longer_owns_ags_app_launchers(self) -> None:
        tasks = (_ROLES_DIR / "cli_tools" / "tasks" / "main.yml").read_text()
        assert "cli_tools_legacy_app_names" not in tasks
        for launcher in (
            "capture-ui.j2",
            "clipboard-ui.j2",
            "wallpaper-selector-ui.j2",
            "icon-color-mapping-editor.j2",
            "btop-theme-studio.j2",
        ):
            assert not (_ROLES_DIR / "cli_tools" / "templates" / launcher).exists()
        assert "ags-run-locked" in tasks

    def test_gui_tools_owns_no_ags_app_lifecycle(self) -> None:
        tasks = (_ROLES_DIR / "gui_tools" / "tasks" / "main.yml").read_text()
        variables = (_ROLES_DIR / "gui_tools" / "vars" / "main.yml").read_text()
        assert "gui_tools_ags_instances" not in variables
        assert "gui_tools_ags_always_on" not in variables
        assert "ags quit" not in tasks
        assert "ags run" not in tasks
        # dunst must still be out of the way before notifications starts.
        assert "dunst.service" in variables
        assert "mask dunst.service" in tasks

    def test_config_links_owns_no_ags_app_dirs(self) -> None:
        variables = (_ROLES_DIR / "config_links" / "vars" / "main.yml").read_text()
        for basename in (
            "ags",
            "ags-capture",
            "ags-icme",
            "ags-clipboard",
            "ags-wallpaper-selector",
            "ags-notifications",
            "ags-btop-studio",
        ):
            assert f"  - {basename}\n" not in variables, basename
        tasks = (_ROLES_DIR / "config_links" / "tasks" / "main.yml").read_text()
        assert "apps.yaml" not in tasks

    def test_compositor_configs_does_not_generate_ags_artifacts(self) -> None:
        tasks = (_ROLES_DIR / "compositor_configs" / "tasks" / "main.yml").read_text()
        assert "compositor_configs_icon_manifest" not in tasks
        assert "ags-bar-validate" not in tasks
        assert "apps.yaml" not in tasks

    def test_filesystem_does_not_claim_the_ags_xdg_dir(self) -> None:
        variables = (_ROLES_DIR / "filesystem" / "vars" / "main.yml").read_text()
        assert '"{{ filesystem_xdg_config_home }}/ags"' not in variables


class TestLauncherTemplate:
    def test_generic_launcher_is_lock_routed_and_toggle_aware(self) -> None:
        text = (_ROLE / "templates" / "ags-app-launcher.j2").read_text()
        assert "ags-run-locked" in text
        assert "exec ags run" not in text
        assert "ags run -d" not in text
        # Warm instance: request toggle (clipboard) and window toggle (the
        # other apps), never a restart.
        assert 'ags request "$1"' in text
        assert "ags toggle" in text
        assert '"${INSTANCE}-window"' in text
        assert '"${CONFIG_BASENAME#ags-}-window"' in text
        # Cold start: reveal a start-hidden overlay through its request surface.
        assert 'request show' in text

    def test_launcher_renders_every_app_list_launcher(self) -> None:
        text = (_ROLE / "tasks" / "_one.yml").read_text()
        assert "ags-app-launcher.j2" in text
        assert "app.launcher" in text

    def test_verify_mirror_splits_the_autostart_surface_by_launch_policy(
        self,
    ) -> None:
        verify_one = (_ROLES_DIR / "verify" / "tasks" / "_verify_standalone.yml").read_text()
        assert "app.autostart" in verify_one
        assert "--expect-instance " in verify_one
        assert "ags-run-locked" in verify_one
        assert "app.launch == 'always'" in verify_one
        assert "| length - 1) == 0" in verify_one
        assert "app.launch == 'on-demand'" in verify_one
        assert "| length - 1) == 1" in verify_one

    def test_verify_mirror_covers_all_standalone_surfaces(self) -> None:
        verify_tasks = (_ROLES_DIR / "verify" / "tasks" / "main.yml").read_text()
        assert "_verify_standalone.yml" in verify_tasks
        verify_one = (_ROLES_DIR / "verify" / "tasks" / "_verify_standalone.yml").read_text()
        for needle in (
            "app.installDir",
            "app.tag",
            "verify_ags_apps_units_platform_shortcut",
            "appearance-refresh",
            "icons.json",
            "autostart",
            "ags-run-locked",
        ):
            assert needle in verify_one, f"verify mirror misses {needle!r}"


class TestAlwaysOnUnits:
    """REQ-023: the two always-on apps are systemd --user units."""

    @staticmethod
    def _all_nested_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        flattened: list[dict[str, Any]] = []
        for task in tasks:
            flattened.append(task)
            for key in ("block", "rescue", "always"):
                if isinstance(task.get(key), list):
                    flattened.extend(TestAlwaysOnUnits._all_nested_tasks(task[key]))
        return flattened

    def test_role_renders_enables_and_starts_always_on_units(self) -> None:
        one = self._all_nested_tasks(_tasks_file("_one.yml"))
        text = (_ROLE / "tasks" / "_one.yml").read_text()
        assert "dotfiles-ags-app.service.j2" in text
        assert "ags_apps_units_unit_file" in text
        assert "ags_apps_units_unit_wants_link" in text
        assert "default.target.wants" in (_ROLE / "vars" / "main.yml").read_text()

        template_tasks = [
            task
            for task in one
            if _module_key(task) == "ansible.builtin.template"
            and _module(task).get("src") == "dotfiles-ags-app.service.j2"
        ]
        assert len(template_tasks) == 1
        assert "app.launch == 'always'" in str(template_tasks[0].get("when"))

        enable_tasks = [
            task
            for task in one
            if _module_key(task) == "ansible.builtin.command"
            and "enable" in list(_module(task).get("argv", []))
        ]
        assert len(enable_tasks) == 1
        assert _module(enable_tasks[0])["argv"][-1] == "{{ ags_apps_units_unit_name }}"
        enable_when = " ".join(str(clause) for clause in enable_tasks[0].get("when", []))
        assert "app.launch == 'always'" in enable_when
        assert "ags_apps_units_manager_probe.rc" in enable_when

        start_tasks = [
            task
            for task in one
            if _module_key(task) == "ansible.builtin.command"
            and list(_module(task).get("argv", []))[:3]
            == ["systemctl", "--user", "start"]
        ]
        assert len(start_tasks) == 1, "expected one explicit systemctl --user start"
        assert _module(start_tasks[0])["argv"][-1] == "{{ ags_apps_units_unit_name }}"
        start_when = " ".join(str(clause) for clause in start_tasks[0].get("when", []))
        assert "app.launch == 'always'" in start_when
        assert "ags_apps_units_manager_probe.rc" in start_when

    def test_quiesce_stops_the_owning_unit_before_the_link_repoint(self) -> None:
        quiesce = (_ROLE / "tasks" / "_quiesce.yml").read_text()
        assert "systemctl --user stop" in quiesce
        assert 'systemctl --user stop "$AGS_UNIT"' in quiesce
        assert quiesce.index("systemctl --user stop") < quiesce.index("ags quit -i")
        assert "systemctl --user is-active --quiet" in quiesce
        assert "stayed active after systemctl --user stop" in quiesce
        assert "systemctl --user stop '$AGS_UNIT' failed" in quiesce

        one = self._all_nested_tasks(_tasks_file("_one.yml"))
        quiesce_index = next(
            i
            for i, task in enumerate(one)
            if _module_key(task) == "ansible.builtin.include_tasks"
            and _module(task).get("_raw") == "_quiesce.yml"
        )
        spine_index = next(
            i for i, task in enumerate(one) if "repoint the spine link" in str(task.get("name"))
        )
        start_index = next(
            i
            for i, task in enumerate(one)
            if _module_key(task) == "ansible.builtin.command"
            and list(_module(task).get("argv", []))[:3]
            == ["systemctl", "--user", "start"]
        )
        assert quiesce_index < spine_index < start_index

    def test_explicit_start_refuses_an_already_active_unit(self) -> None:
        one = self._all_nested_tasks(_tasks_file("_one.yml"))
        prestart = next(
            task
            for task in one
            if _module_key(task) == "ansible.builtin.command"
            and list(_module(task).get("argv", []))[:4]
            == ["systemctl", "--user", "is-active", "--quiet"]
        )
        assert prestart.get("register") == "ags_apps_units_unit_prestart"
        assert prestart.get("failed_when") is False

        guard = next(
            task
            for task in one
            if _module_key(task) == "ansible.builtin.assert"
            and "refuse an already-active unit" in str(task.get("name"))
        )
        assert "ags_apps_units_unit_prestart.rc" in str(_module(guard)["that"])
        assert "still active" in str(_module(guard).get("fail_msg"))

    def test_failed_start_surfaces(self) -> None:
        one = self._all_nested_tasks(_tasks_file("_one.yml"))
        start = next(
            task
            for task in one
            if _module_key(task) == "ansible.builtin.command"
            and list(_module(task).get("argv", []))[:3]
            == ["systemctl", "--user", "start"]
        )
        assert start.get("failed_when") is False

        poststart = next(
            task
            for task in one
            if _module_key(task) == "ansible.builtin.command"
            and list(_module(task).get("argv", []))[:3]
            == ["systemctl", "--user", "show"]
        )
        assert "ActiveState" in str(_module(poststart).get("argv"))
        assert "MainPID" in str(_module(poststart).get("argv"))

        assert_task = next(
            task
            for task in one
            if _module_key(task) == "ansible.builtin.assert"
            and "explicit start brought the new unit up" in str(task.get("name"))
        )
        terms = str(_module(assert_task)["that"])
        assert "ags_apps_units_unit_start.rc" in terms
        assert "equalto', 'active'" in terms
        assert "MainPID" not in terms  # the PID is the numeric stdout line
        assert "not active with a main PID" in str(_module(assert_task).get("fail_msg"))

    def test_stop_timeout_surfaces(self) -> None:
        quiesce = (_ROLE / "tasks" / "_quiesce.yml").read_text()
        assert "for _ in $(seq 1 40)" in quiesce
        assert "stayed active after systemctl --user stop" in quiesce
        assert "exit 1" in quiesce
        template = (_ROLE / "templates" / "dotfiles-ags-app.service.j2").read_text()
        assert "TimeoutStopSec={{ ags_apps_units_timeout_stop_sec }}" in template
        variables = yaml.safe_load((_ROLE / "vars" / "main.yml").read_text())
        assert variables["ags_apps_units_timeout_stop_sec"] == 10

    def test_managerless_hosts_keep_the_wants_link_path(self) -> None:
        one = self._all_nested_tasks(_tasks_file("_one.yml"))
        wants = next(
            task
            for task in one
            if _module_key(task) == "ansible.builtin.file"
            and _module(task).get("dest") == "{{ ags_apps_units_unit_wants_link }}"
        )
        wants_when = " ".join(str(clause) for clause in wants.get("when", []))
        assert "ags_apps_units_manager_probe.rc" in wants_when
        assert "!= 0" in wants_when

        lifecycle = [
            task
            for task in one
            if _module_key(task) == "ansible.builtin.command"
            and list(_module(task).get("argv", []))[:2] == ["systemctl", "--user"]
        ]
        assert lifecycle
        for task in lifecycle:
            when_text = " ".join(str(clause) for clause in task.get("when", []))
            assert "app.launch == 'always'" in when_text, task.get("name")
            assert "ags_apps_units_manager_probe.rc" in when_text, task.get("name")

    def test_no_raw_always_on_start_remains(self) -> None:
        one = self._all_nested_tasks(_tasks_file("_one.yml"))
        raw_start = [
            task
            for task in one
            if _module_key(task) == "ansible.builtin.command"
            and "ags_apps_units_run_locked" in str(_module(task).get("argv", []))
        ]
        assert len(raw_start) == 1, "expected only the on-demand cutover start"
        when = " ".join(str(clause) for clause in raw_start[0].get("when", []))
        assert "app.launch == 'on-demand'" in when
        assert "app.launch == 'always'" not in when

    def test_rollback_uses_the_unit_for_always_on_apps(self) -> None:
        rollback = _tasks_file("_rollback.yml")
        unit_restart = [
            task
            for task in rollback
            if _module_key(task) == "ansible.builtin.systemd"
        ]
        assert len(unit_restart) == 1
        when = " ".join(str(clause) for clause in unit_restart[0].get("when", []))
        assert "app.launch == 'always'" in when
        raw_restart = [
            task
            for task in rollback
            if _module_key(task) == "ansible.builtin.command"
            and "ags_apps_units_run_locked" in str(_module(task).get("argv", []))
        ]
        assert len(raw_restart) == 1
        when = " ".join(str(clause) for clause in raw_restart[0].get("when", []))
        assert "app.launch == 'on-demand'" in when

    def test_unit_vars_pin_the_frozen_policy(self) -> None:
        data = yaml.safe_load((_ROLE / "vars" / "main.yml").read_text())
        assert data["ags_apps_units_ags_bin"] == "/usr/bin/ags"
        assert data["ags_apps_units_restart_sec"] == 2
        assert data["ags_apps_units_timeout_stop_sec"] == 10
        assert data["ags_apps_units_unit_prefix"] == "dotfiles-ags"
        assert data["ags_apps_units_unit_name"] == "{{ ags_apps_units_unit_prefix }}-{{ app.app }}.service"


# ── GUI-free execution harness ──────────────────────────────────────────────


def _sha256_tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.parts
    }


def _fake_ags(bin_dir: Path) -> Path:
    path = bin_dir / "ags"
    path.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
REG="${FAKE_AGS_REGISTRY:?}"
CALLS="${FAKE_AGS_CALLS:-$REG.calls}"
WINDOWS="${FAKE_AGS_WINDOWS:-$REG.windows}"
TOGGLES="${FAKE_AGS_REQUEST_TOGGLES:-$REG.request-toggles}"
mkdir -p "$(dirname "$REG")"
touch "$REG" "$CALLS" "$WINDOWS" "$TOGGLES"
log() { printf '%s\\n' "$*" >> "$CALLS"; }
case "$1" in
  list) cat "$REG" ;;
  quit)
    shift
    name=""
    while [ "$#" -gt 0 ]; do
      case "$1" in -i) name="$2"; shift 2 ;; *) shift ;; esac
    done
    log "quit $name"
    [ -n "$name" ] || exit 0
    grep -vx "$name" "$REG" > "$REG.tmp" 2>/dev/null || true
    mv "$REG.tmp" "$REG"
    pidfile="$REG.$name.pid"
    if [ -f "$pidfile" ]; then
      kill "$(cat "$pidfile")" 2>/dev/null || true
      rm -f "$pidfile"
    fi
    ;;
  run)
    shift
    dir=""
    while [ "$#" -gt 0 ]; do
      case "$1" in
        -d) dir="$2"; shift 2 ;;
        --log-file) shift 2 ;;
        *) shift ;;
      esac
    done
    [ -n "$dir" ] || { echo "fake ags: missing -d" >&2; exit 2; }
    name="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["instance"])' "$dir/app.manifest.json")"
    log "run $name"
    echo "$name" >> "$REG"
    echo "$$" > "$REG.$name.pid"
    trap 'grep -vx "$name" "$REG" > "$REG.tmp" 2>/dev/null || true; mv "$REG.tmp" "$REG"; rm -f "$REG.$name.pid"; exit 0' TERM INT
    sleep "${FAKE_AGS_RUN_SECONDS:-60}" &
    wait $!
    ;;
  request)
    argv=()
    shift
    while [ "$#" -gt 0 ]; do
      case "$1" in -i) shift 2 ;; *) argv+=("$1"); shift ;; esac
    done
    log "request ${argv[*]}"
    if [ "${argv[0]:-}" = "appearance-refresh" ]; then
      python3 -c 'import json,sys; print(json.dumps({"deferred":"no generation yet","genHash":sys.argv[1]}))' "${argv[1]:-}"
      exit 0
    fi
    if [ "${argv[0]:-}" = "toggle" ] && grep -qx "${argv[0]}" "$TOGGLES" 2>/dev/null; then
      echo "ok"
      exit 0
    fi
    if [ "${argv[0]:-}" = "show" ] && grep -qx "show" "$TOGGLES" 2>/dev/null; then
      echo "ok"
      exit 0
    fi
    echo "unknown request: ${argv[*]}"
    ;;
  toggle)
    shift
    window=""
    while [ "$#" -gt 0 ]; do
      case "$1" in
        -i) shift 2 ;;
        *)
          if [ -z "$window" ]; then window="$1"; fi
          shift
          ;;
      esac
    done
    log "toggle $window"
    if [ -n "$window" ] && grep -qx "$window" "$WINDOWS" 2>/dev/null; then
      exit 0
    fi
    echo "no window registered with name \\"$window\\"" >&2
    exit 1
    ;;
  *) exit 0 ;;
esac
""",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def _write_wrapper(bin_dir: Path) -> None:
    shutil.copy(_ROLES_DIR / "cli_tools" / "files" / "ags-run-locked", bin_dir / "ags-run-locked")
    (bin_dir / "ags-run-locked").chmod(0o755)


def _force_managerless(bin_dir: Path) -> None:
    """Make the role's `systemctl --user` probe deterministic.

    These tests exercise the manager-less enablement path (the R-6 case): the
    unit is rendered and linked into default.target.wants, but nothing calls a
    real user manager. A stub that always fails keeps a developer's live
    session out of the test and avoids starting real units on the host.
    """
    path = bin_dir / "systemctl"
    path.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    path.chmod(0o755)


def _fake_manager(bin_dir: Path) -> None:
    """Install a fake `systemctl --user` that simulates a unit lifecycle.

    It records every stop/start with the link target resolved at that moment,
    so a test can prove the cutover stopped the OLD tag and started the NEW
    link. `start` registers the instance on the fake AGS bus just like the real
    unit would (via ExecStart); `stop` runs the unit's ExecStop equivalent
    (`ags quit -i <instance>`).

    Failure injection (environment):
      FAKE_SYSTEMD_FAIL_START=1  -> `start` exits 1, leaves the unit inactive.
      FAKE_SYSTEMD_STOP_NOOP=1   -> `stop` returns 0 but leaves the unit active
                                    (the bounded-wait "stop timeout" path).
    """
    path = bin_dir / "systemctl"
    path.write_text(
        """#!/usr/bin/env bash
set -u
STATE="${FAKE_SYSTEMD_STATE:?}"
LOG="${FAKE_SYSTEMD_CALLS:?}"
UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$STATE" "$(dirname "$LOG")"
touch "$LOG"
log() { printf '%s\\n' "$*" >> "$LOG"; }

if [ "${1:-}" = "--user" ]; then shift; fi
cmd="${1:-}"
[ "$#" -gt 0 ] && shift

state_file() { printf '%s/%s.state' "$STATE" "$1"; }
unit_instance() {
    local unit_file="$UNIT_DIR/$1"
    [ -f "$unit_file" ] || return 0
    grep -o -- '--expect-instance [^ ]*' "$unit_file" | head -1 | awk '{print $2}'
}
unit_spine() {
    local unit_file="$UNIT_DIR/$1"
    [ -f "$unit_file" ] || return 0
    sed -n 's|.*-- /usr/bin/ags run -d \\([^ ]*\\).*|\\1|p' "$unit_file" | head -1
}
current_link() {
    local spine="$1"
    if [ -n "$spine" ]; then
        readlink -f "$spine" 2>/dev/null || true
    fi
}
case "$cmd" in
    show-environment) exit 0 ;;
    daemon-reload) log "daemon-reload"; exit 0 ;;
    reset-failed) log "reset-failed $*"; exit 0 ;;
    enable)
        unit="${1:-}"
        [ -n "$unit" ] || exit 1
        mkdir -p "$UNIT_DIR/default.target.wants"
        ln -sfn "$UNIT_DIR/$unit" "$UNIT_DIR/default.target.wants/$unit"
        log "enable $unit"
        exit 0
        ;;
    stop)
        unit="${1:-}"
        [ -n "$unit" ] || exit 1
        inst="$(unit_instance "$unit")"
        spine="$(unit_spine "$unit")"
        log "stop $unit link=$(current_link "$spine") instance=$inst"
        if [ "${FAKE_SYSTEMD_STOP_NOOP:-0}" = "1" ]; then
            printf 'active\\n' > "$(state_file "$unit")"
            exit 0
        fi
        if [ "${FAKE_SYSTEMD_FAIL_STOP:-0}" = "1" ]; then
            printf 'active\\n' > "$(state_file "$unit")"
            exit 1
        fi
        if [ -n "$inst" ]; then
            ags quit -i "$inst" >/dev/null 2>&1 || true
        fi
        printf 'inactive\\n' > "$(state_file "$unit")"
        exit 0
        ;;
    start)
        unit="${1:-}"
        [ -n "$unit" ] || exit 1
        state="$(cat "$(state_file "$unit")" 2>/dev/null || echo inactive)"
        inst="$(unit_instance "$unit")"
        spine="$(unit_spine "$unit")"
        log "start $unit link=$(current_link "$spine") instance=$inst state=$state"
        if [ "${FAKE_SYSTEMD_FAIL_START:-0}" = "1" ]; then
            printf 'inactive\\n' > "$(state_file "$unit")"
            exit 1
        fi
        if [ "$state" = "active" ]; then
            exit 0
        fi
        if [ -n "$inst" ]; then
            printf '%s\\n' "$inst" >> "${FAKE_AGS_REGISTRY:?}"
        fi
        printf 'active\\n' > "$(state_file "$unit")"
        exit 0
        ;;
    is-active)
        if [ "${1:-}" = "--quiet" ]; then shift; fi
        unit="${1:-}"
        if [ "$(cat "$(state_file "$unit")" 2>/dev/null || echo inactive)" = "active" ]; then
            exit 0
        fi
        exit 3
        ;;
    show)
        unit=""
        for arg in "$@"; do unit="$arg"; done
        state="$(cat "$(state_file "$unit")" 2>/dev/null || echo inactive)"
        log "show $unit state=$state"
        if [ "$state" = "active" ]; then
            printf 'active\\n4242\\n'
        else
            printf 'inactive\\n0\\n'
        fi
        exit 0
        ;;
    *)
        log "other $cmd $*"
        exit 0
        ;;
esac
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _make_app_repo(
    root: Path,
    name: str,
    *,
    app: str | None = None,
    instance: str | None = None,
    config_dir: str | None = None,
    bin_link: str | None = None,
    colors_pointer: Path | None = None,
    include_bin_tool: bool = True,
    icons_json: str | None = None,
    tag: str,
) -> Path:
    app = app or name
    instance = instance or name
    config_dir = config_dir or f"ags-{name}"
    repo = root / "repos" / name
    shutil.copytree(_FAKE_APP, repo)
    fixture_tool = repo / "bin" / "fake-app-tool"
    if include_bin_tool:
        if bin_link:
            fixture_tool.rename(repo / "bin" / bin_link)
    else:
        fixture_tool.unlink()
    (repo / "app.tsx").write_text(
        (repo / "app.tsx").read_text(encoding="utf-8").replace("__INSTANCE__", instance),
        encoding="utf-8",
    )
    manifest = json.loads((repo / "app.manifest.json").read_text(encoding="utf-8"))
    manifest.update({"app": app, "instance": instance, "configDir": config_dir})
    (repo / "app.manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if icons_json is not None:
        (repo / "icons.json").write_text(icons_json, encoding="utf-8")
    if colors_pointer is not None:
        (repo / "colors.css").symlink_to(colors_pointer)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.email=t@example.invalid",
            "-c",
            "user.name=test",
            "commit",
            "-qm",
            "fake",
        ],
        check=True,
    )
    subprocess.run(["git", "-C", str(repo), "tag", tag], check=True)
    return repo


def _write_composition(
    root: Path,
    repos: dict[str, Path],
    *,
    tags: dict[str, str] | None = None,
    fixture: str = "all-standalone.apps.yaml",
    apps: tuple[str, ...] | None = None,
) -> Path:
    """Write the composition app list with per-test repo/tag overrides."""
    provisioning = root / "composition" / "dotfiles" / "provisioning"
    provisioning.mkdir(parents=True, exist_ok=True)
    document = yaml.safe_load((_APP_LISTS / fixture).read_text(encoding="utf-8"))
    if apps is not None:
        document["apps"] = [entry for entry in document["apps"] if entry["app"] in apps]
    tags = tags or {}
    for entry in document["apps"]:
        app_id = entry["app"]
        if app_id in repos:
            entry["repo"] = str(repos[app_id])
        if app_id in tags:
            entry["tag"] = tags[app_id]
    (provisioning / "apps.yaml").write_text(
        yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
    )
    (provisioning / "program-tuple.yaml").write_text(
        "schemaVersion: 1\nags-platform: v1.0.0\ncontracts: v0.8.0\ndotfiles-assets: v0.13.0\n",
        encoding="utf-8",
    )
    return provisioning


def _stage_fake_platform(install: Path, icons_json: str = '{"schemaVersion": 1}\n') -> Path:
    unit = install / "ags-platform" / "v1.0.0"
    unit.mkdir(parents=True)
    (unit / "index.ts").write_text("", encoding="utf-8")
    (unit / "icons.json").write_text(icons_json, encoding="utf-8")
    return unit


def _stage_autostart_text(install: Path, text: str) -> Path:
    path = install / "config" / "hypr" / "autostart.lua"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _stage_autostart(install: Path) -> Path:
    """Install the verbatim assets v0.12.1 autostart fixture (never written by a role)."""
    return _stage_autostart_text(install, _ASSETS_AUTOSTART.read_text(encoding="utf-8"))


def _run_role(
    tmp_path: Path,
    provisioning: Path,
    *,
    cutover: bool = False,
    check: bool = False,
    manager: bool = False,
    extra_env: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    ansible_playbook = shutil.which("ansible-playbook")
    if ansible_playbook is None:
        pytest.skip("ansible-playbook not installed; skipping execution test")
    install = tmp_path / "install"
    home = tmp_path / "home"
    xdg = tmp_path / "xdg"
    state = tmp_path / "state"
    bin_dir = tmp_path / "bin"
    runtime = tmp_path / "runtime"
    for path in (home, xdg, state, bin_dir, runtime):
        path.mkdir(exist_ok=True)
    _fake_ags(bin_dir)
    _write_wrapper(bin_dir)
    if manager:
        _fake_manager(bin_dir)
    else:
        _force_managerless(bin_dir)
    systemd_state = tmp_path / "fake-systemd-state"
    systemd_calls = tmp_path / "fake-systemd-calls"
    registry = tmp_path / "fake-ags-registry"
    env = dict(
        os.environ,
        HOME=str(home),
        XDG_CONFIG_HOME=str(xdg),
        XDG_STATE_HOME=str(state),
        XDG_RUNTIME_DIR=str(runtime),
        UV_TOOL_BIN_DIR=str(bin_dir),
        FAKE_AGS_REGISTRY=str(registry),
        FAKE_AGS_CALLS=str(tmp_path / "fake-ags-calls"),
        FAKE_AGS_WINDOWS=str(tmp_path / "fake-ags-windows"),
        FAKE_AGS_REQUEST_TOGGLES=str(tmp_path / "fake-ags-request-toggles"),
        FAKE_AGS_RUN_SECONDS="30",
        FAKE_SYSTEMD_STATE=str(systemd_state),
        FAKE_SYSTEMD_CALLS=str(systemd_calls),
        ANSIBLE_CONFIG=str(_ANSIBLE_DIR / "ansible.cfg"),
        PATH=f"{bin_dir}:{os.environ.get('PATH', '')}",
    )
    if extra_env:
        env.update(extra_env)
    args = [
        ansible_playbook,
        str(_ANSIBLE_DIR / "playbooks" / "ags-apps-units.yaml"),
        "-e",
        f"install_dir={install}",
        "-e",
        f"manifests_dir={provisioning}",
        "-e",
        f"composition_root={tmp_path / 'composition'}",
        "-e",
        f"ags_apps_units_cutover={'true' if cutover else 'false'}",
    ]
    if check:
        args.insert(2, "--check")
    result = subprocess.run(args, capture_output=True, text=True, env=env, timeout=240)
    return result, {
        "install": str(install),
        "xdg": str(xdg),
        "bin": str(bin_dir),
        "state": str(state),
        "runtime": str(runtime),
        "registry": str(registry),
        "home": str(home),
        "systemd_state": str(systemd_state),
        "systemd_calls": str(systemd_calls),
    }


def _stage_seven_app_repos(tmp_path: Path) -> tuple[dict[str, Path], Path]:
    """Build the seven fake app repos (v3: no palette pointer inside a tag)."""
    repos: dict[str, Path] = {}
    icons = None
    for entry in _app_list():
        app_id = entry["app"]
        icons_json = (_FAKE_APP / "icons.json").read_text(encoding="utf-8")
        if app_id == "bar":
            icons = icons_json
        repos[app_id] = _make_app_repo(
            tmp_path,
            app_id,
            app=app_id,
            instance=entry["instance"],
            config_dir=entry["configDir"],
            bin_link=entry.get("binLink"),
            icons_json=icons_json if app_id == "bar" else None,
            tag=entry["tag"],
        )
    return repos, icons or ""


def _stage_bar_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Stage the bar-only composition used by the always-on cutover tests."""
    entry = next(entry for entry in _app_list() if entry["app"] == "bar")
    icons = (_FAKE_APP / "icons.json").read_text(encoding="utf-8")
    repo = _make_app_repo(
        tmp_path,
        "bar",
        app="bar",
        instance=entry["instance"],
        config_dir=entry["configDir"],
        icons_json=icons,
        tag=entry["tag"],
    )
    provisioning = _write_composition(tmp_path, {"bar": repo}, apps=("bar",))
    install = tmp_path / "install"
    _stage_fake_platform(install, icons_json=icons)
    _stage_autostart(install)
    return repo, provisioning, install


def _bump_tag(tmp_path: Path, repo: Path, tag: str) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.email=t@example.invalid",
            "-c",
            "user.name=test",
            "commit",
            "--allow-empty",
            "-qm",
            tag,
        ],
        check=True,
    )
    subprocess.run(["git", "-C", str(repo), "tag", tag], check=True)


def _stop_fake_ags(paths: dict[str, str]) -> None:
    registry = Path(paths["registry"])
    if not registry.exists():
        return
    for pidfile in registry.parent.glob(registry.name + ".*.pid"):
        try:
            os.kill(int(pidfile.read_text().strip()), 15)
        except (OSError, ValueError):
            pass
        pidfile.unlink(missing_ok=True)
    registry.unlink(missing_ok=True)


class TestRoleExecution:
    def test_check_mode_is_dry_on_a_fresh_host(self, tmp_path: Path) -> None:
        """A fresh-host --check must not fail on a tag/link it did not create:
        the verifications that read installed state are check-gated."""
        install = tmp_path / "install"
        repos, bar_icons = _stage_seven_app_repos(tmp_path)
        provisioning = _write_composition(tmp_path, repos)
        _stage_fake_platform(install, icons_json=bar_icons)
        _stage_autostart(install)
        result, paths = _run_role(tmp_path, provisioning, check=True)
        assert result.returncode == 0, result.stdout + result.stderr
        assert not (install / "apps").exists(), "a dry run must not install an app"
        assert not (Path(paths["xdg"]) / "ags").exists(), "a dry run must not link"

    def test_all_seven_apps_install_the_full_topology(self, tmp_path: Path) -> None:
        install = tmp_path / "install"
        repos, bar_icons = _stage_seven_app_repos(tmp_path)
        provisioning = _write_composition(tmp_path, repos)
        _stage_fake_platform(install, icons_json=bar_icons)
        _stage_autostart(install)
        result, paths = _run_role(tmp_path, provisioning, cutover=True)
        try:
            assert result.returncode == 0, result.stdout + result.stderr
            apps = {entry["app"]: entry for entry in _app_list()}
            for app_id, entry in apps.items():
                unit = install / "apps" / entry["installDir"] / entry["tag"]
                spine = install / "config" / entry["spineLink"]
                xdg = Path(paths["xdg"]) / entry["xdgLink"]
                assert (unit / "app.tsx").is_file(), app_id
                assert not (unit / ".git").exists(), app_id
                assert (install / "apps" / entry["installDir"] / "pinned").read_text().strip() == entry["tag"]
                assert spine.is_symlink() and os.readlink(spine) == str(unit), app_id
                assert xdg.is_symlink() and os.readlink(xdg) == str(spine), app_id
                if "binLink" in entry:
                    link = Path(paths["bin"]) / entry["binLink"]
                    assert link.is_symlink()
                    assert os.readlink(link) == str(unit / "bin" / entry["binLink"])
                if "launcher" in entry:
                    launcher = Path(paths["bin"]) / entry["launcher"]
                    text = launcher.read_text()
                    assert f'INSTANCE="{entry["instance"]}"' in text
                    assert str(xdg) in text
                    assert "ags-run-locked" in text

            shortcut = install / "apps" / "node_modules" / "ags-platform"
            assert shortcut.is_symlink()
            assert os.readlink(shortcut) == str(install / "ags-platform" / "v1.0.0")

            bar_tag = apps["bar"]["tag"]
            assert os.readlink(install / "config" / "ags") == str(
                install / "apps" / "bar" / bar_tag
            )
            bar_unit = install / "apps" / "bar" / bar_tag
            assert not (bar_unit / "colors.css").exists(), (
                "v3: no runtime palette pointer may live inside an app tag"
            )
            assert not (bar_unit / "appearance.css").exists()
            assert (bar_unit / "icons.json").read_bytes() == bar_icons.encode()

            # REQ-023: always-on apps are systemd --user units. This harness
            # forces the manager-less path, so the units are installed and
            # enabled (wants link) but not started; no raw wrapper launch may
            # leave them on the bus. Every on-demand app was started for the
            # cutover proof and stopped again.
            user_units = Path(paths["home"]) / ".config" / "systemd" / "user"
            for unit_name, config_dir in (
                ("dotfiles-ags-bar.service", "ags"),
                ("dotfiles-ags-notifications.service", "ags-notifications"),
            ):
                unit_file = user_units / unit_name
                wants = user_units / "default.target.wants" / unit_name
                assert unit_file.is_file(), unit_name
                assert wants.is_symlink(), unit_name
                assert os.readlink(wants) == str(unit_file)
                text = unit_file.read_text()
                assert "--exec" in text
                assert f"/usr/bin/ags run -d {install}/config/{config_dir}" in text
                assert "ExecStop=/usr/bin/ags quit -i " in text
            assert (
                not Path(paths["registry"]).exists()
                or Path(paths["registry"]).read_text().strip() == ""
            ), "manager-less install must not raw-start an always-on app"
            # No legacy monorepo surface was created by any role.
            assert not (install / "ags-apps").exists()
            assert not (install / "config" / "ags-hypr-pano").exists()
            assert not (Path(paths["bin"]) / "hypr-pano-ui").exists()
        finally:
            _stop_fake_ags(paths)

    def test_active_unit_cutover_stops_old_link_then_starts_new_link(
        self, tmp_path: Path
    ) -> None:
        """BUG-009: an active always-on unit must not survive the relink.

        First install leaves dotfiles-ags-bar.service active on v0.6.0. The tag
        bump then has to stop that unit (logging the OLD link), repoint, and
        explicitly start it (logging the NEW link). `state: started` would have
        been a no-op here.
        """
        repo, provisioning, install = _stage_bar_repo(tmp_path)
        first, paths = _run_role(tmp_path, provisioning, cutover=True, manager=True)
        try:
            assert first.returncode == 0, first.stdout + first.stderr
            calls_first = Path(paths["systemd_calls"]).read_text().splitlines()
            assert not any(
                line.startswith("stop dotfiles-ags-bar.service") for line in calls_first
            ), "an absent/inactive unit must not be stopped"
            assert any(
                line.startswith("start dotfiles-ags-bar.service")
                and "state=inactive" in line
                for line in calls_first
            ), "the first install must explicitly start the inactive unit"
            assert (
                Path(paths["systemd_state"]) / "dotfiles-ags-bar.service.state"
            ).read_text().strip() == "active"

            _bump_tag(tmp_path, repo, "v0.2.0")
            bumped = _write_composition(
                tmp_path, {"bar": repo}, apps=("bar",), tags={"bar": "v0.2.0"}
            )
            second, _ = _run_role(tmp_path, bumped, cutover=True, manager=True)
            assert second.returncode == 0, second.stdout + second.stderr

            old_unit = install / "apps" / "bar" / "v0.6.0"
            new_unit = install / "apps" / "bar" / "v0.2.0"
            calls = Path(paths["systemd_calls"]).read_text().splitlines()
            stop_index = next(
                i
                for i, line in enumerate(calls)
                if line.startswith("stop dotfiles-ags-bar.service")
            )
            start_index = next(
                i
                for i, line in enumerate(calls)
                if i > stop_index and line.startswith("start dotfiles-ags-bar.service")
            )
            assert f"link={old_unit}" in calls[stop_index], calls[stop_index]
            assert f"link={new_unit}" in calls[start_index], calls[start_index]
            assert "state=inactive" in calls[start_index], (
                "the explicit start must not accept the old active unit"
            )
            assert os.readlink(install / "config" / "ags") == str(new_unit)
            assert "ags" in Path(paths["registry"]).read_text().splitlines()
        finally:
            _stop_fake_ags(paths)

    def test_failed_always_on_start_fails_the_cutover(self, tmp_path: Path) -> None:
        _, provisioning, install = _stage_bar_repo(tmp_path)
        result, paths = _run_role(
            tmp_path,
            provisioning,
            cutover=True,
            manager=True,
            extra_env={"FAKE_SYSTEMD_FAIL_START": "1"},
        )
        _stop_fake_ags(paths)
        assert result.returncode != 0
        assert "assert the explicit start brought the new unit up" in result.stdout
        assert "not active with a main PID" in result.stdout
        spine = install / "config" / "ags"
        assert not spine.is_symlink(), "a failed start must roll the links back"

    def test_stop_timeout_fails_before_any_install(self, tmp_path: Path) -> None:
        """A stop that returns 0 but leaves the unit active must fail the
        bounded wait, not proceed to relink/start."""
        _, provisioning, install = _stage_bar_repo(tmp_path)
        home = tmp_path / "home"
        unit_dir = home / ".config" / "systemd" / "user"
        unit_dir.mkdir(parents=True)
        unit_file = unit_dir / "dotfiles-ags-bar.service"
        unit_file.write_text(
            "[Service]\n"
            "ExecStart=/bin/true --expect-instance ags "
            f"-- /usr/bin/ags run -d {install}/config/ags\n"
            "ExecStop=/usr/bin/ags quit -i ags\n",
            encoding="utf-8",
        )
        state = tmp_path / "fake-systemd-state"
        state.mkdir()
        (state / "dotfiles-ags-bar.service.state").write_text("active\n", encoding="utf-8")

        result, paths = _run_role(
            tmp_path,
            provisioning,
            cutover=True,
            manager=True,
            extra_env={"FAKE_SYSTEMD_STOP_NOOP": "1"},
        )
        _stop_fake_ags(paths)
        assert result.returncode != 0
        assert "stayed active after systemctl --user stop" in result.stdout
        assert not (install / "apps" / "bar" / "v0.6.0").exists()

    def test_second_run_does_not_write_inside_installed_tags(self, tmp_path: Path) -> None:
        install = tmp_path / "install"
        repos, bar_icons = _stage_seven_app_repos(tmp_path)
        provisioning = _write_composition(tmp_path, repos)
        _stage_fake_platform(install, icons_json=bar_icons)
        _stage_autostart(install)
        first, paths = _run_role(tmp_path, provisioning, cutover=True)
        try:
            assert first.returncode == 0, first.stdout + first.stderr
            units = [
                install / "apps" / entry["installDir"] / entry["tag"]
                for entry in _app_list()
            ]
            before = {str(path): _sha256_tree(path) for path in units}
            second, _ = _run_role(tmp_path, provisioning, cutover=True)
            assert second.returncode == 0, second.stdout + second.stderr
            after = {str(path): _sha256_tree(path) for path in units}
            assert before == after
        finally:
            _stop_fake_ags(paths)

    def test_reinstall_sweeps_stale_runtime_artifacts_from_an_existing_tag(
        self, tmp_path: Path
    ) -> None:
        """Generations v3 migration: a pre-v3 seeder wrote appearance.css (and
        skin.css/skin.json/colors*) through config/<app> into the tag. The
        reinstall must delete ONLY those runtime artifacts and leave app source
        byte-identical."""
        install = tmp_path / "install"
        repos, bar_icons = _stage_seven_app_repos(tmp_path)
        provisioning = _write_composition(tmp_path, repos)
        _stage_fake_platform(install, icons_json=bar_icons)
        _stage_autostart(install)
        first, paths = _run_role(tmp_path, provisioning, cutover=True)
        try:
            assert first.returncode == 0, first.stdout + first.stderr
            apps = {entry["app"]: entry for entry in _app_list()}
            bar_unit = install / "apps" / apps["bar"]["installDir"] / apps["bar"]["tag"]
            stale = {
                "appearance.css": "/* v2 runtime */\n",
                "skin.css": "/* v2 runtime */\n",
                "skin.json": "{}\n",
                "colors.css": "/* v2 palette pointer */\n",
            }
            for name, body in stale.items():
                (bar_unit / name).write_text(body)
            source_before = {
                str(path.relative_to(bar_unit)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in bar_unit.rglob("*")
                if path.is_file() and path.name not in stale
            }

            second, _ = _run_role(tmp_path, provisioning, cutover=True)
            assert second.returncode == 0, second.stdout + second.stderr
            for name in stale:
                assert not (bar_unit / name).exists(), name
            source_after = {
                str(path.relative_to(bar_unit)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in bar_unit.rglob("*")
                if path.is_file()
            }
            assert source_before == source_after, (
                "the v3 sweep must remove only runtime artifacts; app source "
                "inside the tag must stay byte-identical"
            )
        finally:
            _stop_fake_ags(paths)

    def test_historical_tag_sweep_removes_artifacts_and_preserves_source(
        self, tmp_path: Path
    ) -> None:
        """A v1/v2 runtime left artifacts in OLD tags, not just the pinned one.
        The migration sweep must clean every installed tag directory while
        leaving app source and .git intact; the verify-shaped recursive find
        then matches nothing."""
        install = tmp_path / "install"
        repos, bar_icons = _stage_seven_app_repos(tmp_path)
        provisioning = _write_composition(tmp_path, repos)
        _stage_fake_platform(install, icons_json=bar_icons)
        _stage_autostart(install)
        first, paths = _run_role(tmp_path, provisioning, cutover=True)
        try:
            assert first.returncode == 0, first.stdout + first.stderr
            apps = {entry["app"]: entry for entry in _app_list()}
            bar = apps["bar"]
            old_tag = install / "apps" / bar["installDir"] / "v0.0.1"
            old_tag.mkdir(parents=True)
            (old_tag / "app.tsx").write_text("// historical app source\n", encoding="utf-8")
            (old_tag / "package.json").write_text("{}\n", encoding="utf-8")
            (old_tag / ".git").mkdir()
            (old_tag / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
            artifacts = {
                "appearance.css": "/* v2 runtime */\n",
                "skin.css": "/* v2 runtime */\n",
                "skin.json": "{}\n",
                "tokens.json": "{}\n",
                "colors.css": "/* v2 palette pointer */\n",
                "colors.yaml": "colors: {}\n",
                "colors.btop.theme": "theme\n",
            }
            for name, body in artifacts.items():
                (old_tag / name).write_text(body, encoding="utf-8")
            (old_tag / "colors.rasi").symlink_to(tmp_path / "state" / "palette" / "colors.rasi")
            source_before = {
                str(path.relative_to(old_tag)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in old_tag.rglob("*")
                if path.is_file() and path.name not in artifacts and ".git" not in path.parts
            }

            second, _ = _run_role(tmp_path, provisioning, cutover=True)
            assert second.returncode == 0, second.stdout + second.stderr
            for name in [*artifacts, "colors.rasi"]:
                assert not (old_tag / name).exists(), name
            source_after = {
                str(path.relative_to(old_tag)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in old_tag.rglob("*")
                if path.is_file() and ".git" not in path.parts
            }
            assert source_before == source_after, (
                "the historical-tag sweep must remove only the runtime-artifact "
                "allowlist; app source must stay byte-identical"
            )
            assert (old_tag / ".git" / "HEAD").read_text() == "ref: refs/heads/main\n"
            current_tag = install / "apps" / bar["installDir"] / bar["tag"]
            assert not any((current_tag / name).exists() for name in artifacts), (
                "the current tag must stay clean"
            )
            # The verify gate repeats this recursive find over the apps root.
            remaining = [
                path
                for path in (install / "apps").rglob("*")
                if path.name in {*artifacts, "colors.rasi"}
            ]
            assert remaining == [], remaining
        finally:
            _stop_fake_ags(paths)

    def test_failure_rolls_back_links_and_restarts_the_previous_instance(
        self, tmp_path: Path
    ) -> None:
        install = tmp_path / "install"
        xdg = tmp_path / "xdg"
        old_dir = tmp_path / "old-capture"
        old_dir.mkdir()
        (old_dir / "app.manifest.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "app": "capture",
                    "instance": "capture",
                    "configDir": "ags-capture",
                    "mode": "live",
                    "holdsUnsavedState": False,
                }
            ),
            encoding="utf-8",
        )
        install.mkdir()
        xdg.mkdir()
        (install / "config").mkdir()
        (install / "config" / "ags-capture").symlink_to(old_dir)
        (xdg / "ags-capture").symlink_to(install / "config" / "ags-capture")
        (tmp_path / "fake-ags-registry").write_text("capture\n", encoding="utf-8")
        repos, bar_icons = _stage_seven_app_repos(tmp_path)
        # The capture repo omits its declared bin entry, so the post-repoint
        # surface assertion fails and the rollback block must restore the links.
        capture = repos["capture"]
        (capture / "bin" / "capture-tool").unlink()
        subprocess.run(["git", "-C", str(capture), "add", "-A"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(capture),
                "-c",
                "user.email=t@example.invalid",
                "-c",
                "user.name=test",
                "commit",
                "-qm",
                "drop bin",
            ],
            check=True,
        )
        capture_tag = next(entry["tag"] for entry in _app_list() if entry["app"] == "capture")
        subprocess.run(["git", "-C", str(capture), "tag", "-f", capture_tag], check=True)
        provisioning = _write_composition(tmp_path, repos)
        _stage_fake_platform(install, icons_json=bar_icons)
        _stage_autostart(install)
        result, paths = _run_role(tmp_path, provisioning)
        registry = Path(paths["registry"])
        try:
            assert result.returncode != 0
            assert "rollback restored" in result.stdout.lower()
            assert os.readlink(install / "config" / "ags-capture") == str(old_dir)
            assert os.readlink(xdg / "ags-capture") == str(install / "config" / "ags-capture")
            assert "capture" in registry.read_text().splitlines()
        finally:
            _stop_fake_ags(paths)

    def test_tag_bump_repoints_links_and_preserves_external_state(
        self, tmp_path: Path
    ) -> None:
        install = tmp_path / "install"
        repos, bar_icons = _stage_seven_app_repos(tmp_path)
        provisioning = _write_composition(tmp_path, repos)
        _stage_fake_platform(install, icons_json=bar_icons)
        _stage_autostart(install)
        first, paths = _run_role(tmp_path, provisioning, cutover=True)
        try:
            assert first.returncode == 0, first.stdout + first.stderr
            sentinel = Path(paths["state"]) / "dotfiles" / "current" / "sentinel"
            sentinel.parent.mkdir(parents=True, exist_ok=True)
            sentinel.write_text("external state\n")
            state_before = sentinel.read_text()
            old_units = [
                install / "apps" / entry["installDir"] / entry["tag"]
                for entry in _app_list()
            ]
            before = {str(path): _sha256_tree(path) for path in old_units}

            for repo in repos.values():
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(repo),
                        "-c",
                        "user.email=t@example.invalid",
                        "-c",
                        "user.name=test",
                        "commit",
                        "--allow-empty",
                        "-qm",
                        "v0.2.0",
                    ],
                    check=True,
                )
                subprocess.run(["git", "-C", str(repo), "tag", "v0.2.0"], check=True)

            bumped = _write_composition(
                tmp_path, repos, tags={app_id: "v0.2.0" for app_id in repos}
            )
            second, _ = _run_role(tmp_path, bumped, cutover=True)
            assert second.returncode == 0, second.stdout + second.stderr
            for entry in _app_list():
                new_unit = install / "apps" / entry["installDir"] / "v0.2.0"
                assert (new_unit / "app.tsx").is_file()
                assert (install / "apps" / entry["installDir"] / "pinned").read_text().strip() == "v0.2.0"
                assert os.readlink(install / "config" / entry["spineLink"]) == str(new_unit)
            after = {str(path): _sha256_tree(path) for path in old_units}
            assert before == after, "a tag bump must not mutate an installed tag"
            assert sentinel.read_text() == state_before
        finally:
            _stop_fake_ags(paths)


class TestAutostartLaunchPolicy:
    """AD-32/assets v0.12.1: units own always-on apps; autostart owns overlays."""

    def test_always_on_apps_are_unit_owned_and_absent_from_autostart(
        self, tmp_path: Path
    ) -> None:
        install = tmp_path / "install"
        repos, bar_icons = _stage_seven_app_repos(tmp_path)
        provisioning = _write_composition(
            tmp_path, repos, apps=("bar", "notifications")
        )
        _stage_fake_platform(install, icons_json=bar_icons)
        autostart = _stage_autostart(install)
        result, paths = _run_role(tmp_path, provisioning)
        _stop_fake_ags(paths)
        assert result.returncode == 0, result.stdout + result.stderr

        content = autostart.read_text(encoding="utf-8")
        for identity in ("ags", "notifications"):
            assert content.count(f"--expect-instance {identity}") == 0, identity
        user_units = Path(paths["home"]) / ".config" / "systemd" / "user"
        for unit_name in (
            "dotfiles-ags-bar.service",
            "dotfiles-ags-notifications.service",
        ):
            unit_file = user_units / unit_name
            wants = user_units / "default.target.wants" / unit_name
            assert unit_file.is_file(), unit_name
            assert wants.is_symlink(), unit_name
            assert os.readlink(wants) == str(unit_file)

    def test_always_on_app_with_an_autostart_line_fails(self, tmp_path: Path) -> None:
        install = tmp_path / "install"
        repos, bar_icons = _stage_seven_app_repos(tmp_path)
        provisioning = _write_composition(tmp_path, repos, apps=("bar",))
        _stage_fake_platform(install, icons_json=bar_icons)
        content = _ASSETS_AUTOSTART.read_text(encoding="utf-8")
        _stage_autostart_text(
            install,
            content
            + '    hl.exec_cmd("bash -lc \'$HOME/.local/bin/ags-run-locked '
            "--expect-instance ags'\")\n",
        )
        result, paths = _run_role(tmp_path, provisioning)
        _stop_fake_ags(paths)
        assert result.returncode != 0
        assert (
            "assert autostart never launches an always-on identity"
            in result.stdout
        ), result.stdout + result.stderr
        assert "bar" in result.stdout

    def test_on_demand_locked_autostart_passes(self, tmp_path: Path) -> None:
        install = tmp_path / "install"
        repos, bar_icons = _stage_seven_app_repos(tmp_path)
        provisioning = _write_composition(tmp_path, repos, apps=("bar", "capture"))
        _stage_fake_platform(install, icons_json=bar_icons)
        autostart = _stage_autostart(install)
        result, paths = _run_role(tmp_path, provisioning)
        _stop_fake_ags(paths)
        assert result.returncode == 0, result.stdout + result.stderr
        content = autostart.read_text(encoding="utf-8")
        assert content.count("--expect-instance capture") == 1
        assert content.count("--expect-instance ags") == 0

    def test_on_demand_missing_autostart_line_fails(self, tmp_path: Path) -> None:
        install = tmp_path / "install"
        repos, bar_icons = _stage_seven_app_repos(tmp_path)
        provisioning = _write_composition(tmp_path, repos, apps=("bar", "capture"))
        _stage_fake_platform(install, icons_json=bar_icons)
        content = _ASSETS_AUTOSTART.read_text(encoding="utf-8")
        lines = [
            line
            for line in content.splitlines(keepends=True)
            if "--expect-instance capture" not in line
        ]
        _stage_autostart_text(install, "".join(lines))
        result, paths = _run_role(tmp_path, provisioning)
        _stop_fake_ags(paths)
        assert result.returncode != 0
        assert (
            "assert on-demand autostart launches the identity once under the "
            "shared lock"
        ) in result.stdout, result.stdout + result.stderr
        assert "capture" in result.stdout


class TestLauncherBehavior:
    def _run_launcher(
        self,
        tmp_path: Path,
        launcher_text: str,
        *,
        running: bool,
        windows: tuple[str, ...] = (),
        request_toggles: tuple[str, ...] = (),
    ) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        _fake_ags(bin_dir)
        _write_wrapper(bin_dir)
        registry = tmp_path / "registry"
        calls = tmp_path / "calls"
        windows_file = tmp_path / "windows"
        toggles_file = tmp_path / "request-toggles"
        windows_file.write_text("\n".join(windows) + ("\n" if windows else ""))
        toggles_file.write_text(
            "\n".join(request_toggles) + ("\n" if request_toggles else "")
        )
        if running:
            registry.write_text("fake-app\n")
        launcher = tmp_path / "fake-app-ui"
        launcher.write_text(launcher_text)
        launcher.chmod(0o755)
        env = dict(
            os.environ,
            XDG_RUNTIME_DIR=str(tmp_path / "runtime"),
            FAKE_AGS_REGISTRY=str(registry),
            FAKE_AGS_CALLS=str(calls),
            FAKE_AGS_WINDOWS=str(windows_file),
            FAKE_AGS_REQUEST_TOGGLES=str(toggles_file),
            FAKE_AGS_RUN_SECONDS="1",
            PATH=f"{bin_dir}:{os.environ.get('PATH', '')}",
        )
        (tmp_path / "runtime").mkdir()
        result = subprocess.run(
            [str(launcher)], capture_output=True, text=True, env=env, timeout=60
        )
        lines = calls.read_text().splitlines() if calls.exists() else []
        _stop_fake_ags({"registry": str(registry)})
        return result, lines

    def _render(self, app: dict[str, Any], tmp_path: Path) -> str:
        """Render the generic launcher template for one app entry."""
        from jinja2 import Environment, FileSystemLoader

        xdg = tmp_path / "xdg"
        app_dir = xdg / app["xdgLink"]
        app_dir.mkdir(parents=True)
        (app_dir / "app.manifest.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "app": app["app"],
                    "instance": app["instance"],
                    "configDir": app["configDir"],
                    "mode": "live",
                    "holdsUnsavedState": False,
                }
            ),
            encoding="utf-8",
        )
        env = Environment(
            loader=FileSystemLoader(str(_ROLE / "templates")),
            autoescape=False,
            keep_trailing_newline=True,
        )
        template = env.get_template("ags-app-launcher.j2")
        return template.render(
            app=app,
            ags_apps_units_xdg_config_home=str(xdg),
            ags_apps_units_log_file=str(tmp_path / "state" / "ags" / f"{app['instance']}.log"),
            ags_apps_units_run_locked="ags-run-locked",
            ags_apps_units_lock_timeout=10,
            ags_apps_units_register_timeout=10,
        )

    def test_warm_window_app_toggles_its_window(self, tmp_path: Path) -> None:
        app = next(entry for entry in _app_list() if entry["app"] == "capture")
        # The harness writes INSTANCE=fake-app for both win candidates; render
        # with fake-app so the fake CLI's window list can answer.
        app = {**app, "app": "fake-app", "instance": "fake-app", "xdgLink": "ags-fake-app"}
        result, calls = self._run_launcher(
            tmp_path, self._render(app, tmp_path), running=True, windows=("fake-app-window",)
        )
        assert result.returncode == 0, result.stderr
        assert "toggle fake-app-window" in calls
        assert not any(line.startswith("run ") for line in calls)

    def test_warm_request_app_uses_request_toggle(self, tmp_path: Path) -> None:
        app = {**next(entry for entry in _app_list() if entry["app"] == "clipboard")}
        app = {**app, "app": "fake-app", "instance": "fake-app", "xdgLink": "ags-fake-app"}
        result, calls = self._run_launcher(
            tmp_path, self._render(app, tmp_path), running=True, request_toggles=("toggle",)
        )
        assert result.returncode == 0, result.stderr
        assert "request toggle" in calls
        assert not any(line.startswith("run ") for line in calls)

    def test_warm_icme_falls_back_to_the_config_basename_window(self, tmp_path: Path) -> None:
        app = {**next(entry for entry in _app_list() if entry["app"] == "icme")}
        app = {**app, "app": "fake-app", "instance": "fake-app", "xdgLink": "ags-fake-app"}
        result, calls = self._run_launcher(
            tmp_path, self._render(app, tmp_path), running=True, windows=("fake-app-window",)
        )
        assert result.returncode == 0, result.stderr
        # The instance-derived candidate answers before the config-basename one.
        assert calls.count("toggle fake-app-window") == 1

    def test_cold_start_reveals_a_hidden_overlay(self, tmp_path: Path) -> None:
        app = {**next(entry for entry in _app_list() if entry["app"] == "clipboard")}
        app = {**app, "app": "fake-app", "instance": "fake-app", "xdgLink": "ags-fake-app"}
        result, calls = self._run_launcher(
            tmp_path,
            self._render(app, tmp_path),
            running=False,
            request_toggles=("show",),
        )
        assert result.returncode == 0, result.stderr
        assert "run fake-app" in calls
        assert "request show" in calls
