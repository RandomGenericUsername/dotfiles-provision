"""REQ-047 — GloView activation is an observable systemd user oneshot.

Structural tests (no live systemd/Hyprland): the unit template is rendered with
StrictUndefined and asserted per section, the role's install/enable tasks are
pinned for privilege and graphical-session semantics, and the composition-owned
activator/rebuild scripts are checked for the no-privilege invariant at the
fixture seam.

The authoritative activation contract lives in the composition (dotfiles-v3);
these tests prove the engine deploys it correctly and never adds a second
privileged path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, StrictUndefined

from tests.support import manifests_dir

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
    "until",
    "retries",
    "delay",
    "tags",
    "environment",
    "ignore_errors",
    "notify",
    "check_mode",
}

_RENDER_VARS = {
    "gloview_plugin_bin_dir": "/home/tester/.local/bin",
    "gloview_plugin_unit_name": "dotfiles-gloview.service",
    "gloview_plugin_start_limit_interval_sec": 60,
    "gloview_plugin_start_limit_burst": 3,
    "gloview_plugin_timeout_start_sec": 90,
}


def _find_ansible_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "ansible" / "inventory" / "localhost.yaml"
        if candidate.is_file() and (parent / "pyproject.toml").is_file():
            return parent / "ansible"
    raise FileNotFoundError("ansible/ not found walking up from this test file")


_ANSIBLE_DIR = _find_ansible_dir()
_ROLE_DIR = _ANSIBLE_DIR / "roles" / "gloview_plugin"


def _load_tasks() -> list[dict[str, Any]]:
    data = yaml.safe_load((_ROLE_DIR / "tasks" / "main.yml").read_text())
    assert isinstance(data, list)
    return [dict(entry) for entry in data]


def _load_handlers() -> list[dict[str, Any]]:
    data = yaml.safe_load((_ROLE_DIR / "handlers" / "main.yml").read_text())
    assert isinstance(data, list)
    return [dict(entry) for entry in data]


def _module_key(task: dict[str, Any]) -> str | None:
    for key in task:
        if key not in _TASK_KEYWORDS and key != "with_items":
            return key
    return None


def _render_unit(**overrides: object) -> str:
    template = (_ROLE_DIR / "templates" / "dotfiles-gloview.service.j2").read_text()
    env = Environment(
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env.from_string(template).render(**{**_RENDER_VARS, **overrides})


def _section(rendered: str, name: str) -> str:
    lines = rendered.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == f"[{name}]")
    except StopIteration:
        raise AssertionError(f"section [{name}] missing from rendered unit") from None

    def _is_header(line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith("[") and stripped.endswith("]")

    end = next((i for i in range(start + 1, len(lines)) if _is_header(lines[i])), len(lines))
    return "\n".join(lines[start + 1 : end])


class TestUnitTemplate:
    def test_template_and_handler_exist(self) -> None:
        assert (_ROLE_DIR / "templates" / "dotfiles-gloview.service.j2").is_file()
        assert (_ROLE_DIR / "handlers" / "main.yml").is_file()

    def test_oneshot_remain_after_exit_and_execstart(self) -> None:
        service = _section(_render_unit(), "Service")
        assert "Type=oneshot" in service
        assert "RemainAfterExit=yes" in service
        assert 'ExecStart="/home/tester/.local/bin/gloview-activate"' in service
        assert "TimeoutStartSec=90" in service

    def test_session_scope_and_ordering(self) -> None:
        unit = _section(_render_unit(), "Unit")
        assert "Requires=dbus.socket" in unit
        assert "After=dbus.socket graphical-session.target dotfiles-ags-notifications.service" in unit
        assert "WantedBy=graphical-session.target" in _render_unit()

    def test_start_limits_are_unit_directives(self) -> None:
        unit = _section(_render_unit(), "Unit")
        service = _section(_render_unit(), "Service")
        assert "StartLimitIntervalSec=60" in unit
        assert "StartLimitBurst=3" in unit
        assert "StartLimit" not in service

    def test_unit_has_no_privilege_or_network_invocation(self) -> None:
        rendered = "\n".join(
            line
            for line in _render_unit().splitlines()
            if not line.strip().startswith("#")
        )
        for forbidden in ("sudo", "yay", "pacman", "curl", "wget", "http://", "https://"):
            assert forbidden not in rendered

    def test_unit_does_not_run_the_interactive_helper(self) -> None:
        rendered = "\n".join(
            line
            for line in _render_unit().splitlines()
            if not line.strip().startswith("#")
        )
        assert "gloview-rebuild" not in rendered


class TestRoleTasks:
    def test_tasks_and_handlers_parse_to_named_lists(self) -> None:
        for task in _load_tasks() + _load_handlers():
            assert isinstance(task.get("name"), str) and task["name"]

    def test_installs_unit_and_rebuild_helper_from_composition(self) -> None:
        tasks = _load_tasks()
        template = next(
            task for task in tasks if _module_key(task) == "ansible.builtin.template"
        )
        body = template["ansible.builtin.template"]
        assert body["src"] == "dotfiles-gloview.service.j2"
        assert "gloview_plugin_unit_name" in body["dest"]

        copy = next(
            task
            for task in tasks
            if _module_key(task) == "ansible.builtin.copy"
            and "gloview-rebuild" in str(task)
        )
        copy_body = copy["ansible.builtin.copy"]
        assert "gloview_plugin_scripts_dir" in copy_body["src"]
        assert "gloview-rebuild" in copy_body["src"]
        assert "gloview_plugin_bin_dir" in copy_body["dest"]
        assert copy_body["mode"] == "0755"

    def test_no_become_except_legacy_cleanup(self) -> None:
        for task in _load_tasks():
            name = str(task.get("name", ""))
            if "legacy" in name and "sudoers" in name:
                assert task.get("become") is True
            else:
                assert not task.get("become", False), f"task {name!r} must not use become"

    def test_starts_only_in_an_active_graphical_session(self) -> None:
        tasks = _load_tasks()
        start = next(task for task in tasks if "Start the GloView activation unit" in str(task.get("name")))
        conditions = " ".join(str(item) for item in start.get("when", []))
        assert "gloview_plugin_graphical_probe" in conditions
        assert "gloview_plugin_manager_probe" in conditions
        assert "not ansible_check_mode" in conditions

    def test_handler_is_check_and_session_gated(self) -> None:
        handler = _load_handlers()[0]
        conditions = " ".join(str(item) for item in handler.get("when", []))
        assert "not ansible_check_mode" in conditions
        assert "gloview_plugin_manager_probe" in conditions
        assert "gloview_plugin_graphical_probe" in conditions


class TestCompositionScripts:
    """The fixture is byte-for-byte the composition's script (REQ-047)."""

    _SCRIPTS = manifests_dir() / "scripts"

    def test_activator_never_invokes_privilege_or_network(self) -> None:
        code = "\n".join(
            line
            for line in (self._SCRIPTS / "gloview-activate")
            .read_text(encoding="utf-8")
            .splitlines()
            if not line.strip().startswith("#")
        )
        for forbidden in ("sudo", "pacman", "curl", "wget", "http://", "https://"):
            assert forbidden not in code
        for line in code.splitlines():
            if "yay" in line:
                assert "rebuild_command=" in line, line

    def test_activator_verifies_the_json_plugin_list(self) -> None:
        text = (self._SCRIPTS / "gloview-activate").read_text(encoding="utf-8")
        assert "hyprctl plugin list -j" in text
        assert '"name"[[:space:]]*:[[:space:]]*"GloView"' in text
        assert "$?" not in text, "load exit status must never be the success signal"

    def test_rebuild_helper_is_interactive_and_user_run(self) -> None:
        code = "\n".join(
            line
            for line in (self._SCRIPTS / "gloview-rebuild")
            .read_text(encoding="utf-8")
            .splitlines()
            if not line.strip().startswith("#")
        )
        assert "yay -S --rebuild gloview-git" in code
        assert "Log out and back in" in code
        assert "sudo" not in code
        assert "--noconfirm" not in code
