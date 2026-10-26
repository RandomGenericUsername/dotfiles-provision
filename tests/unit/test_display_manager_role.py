from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.unit import assets_templates

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


def _find_ansible_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "ansible" / "inventory" / "localhost.yaml"
        if candidate.is_file() and (parent / "pyproject.toml").is_file():
            return parent / "ansible"
    raise FileNotFoundError("src/provisioning/ansible/ not found walking up from the test file")


_ANSIBLE_DIR = _find_ansible_dir()
_ROLES_DIR = _ANSIBLE_DIR / "roles" / "display_manager"
_PLAYBOOKS_DIR = _ANSIBLE_DIR / "playbooks"


def _load_tasks() -> list[dict[str, object]]:
    data = yaml.safe_load((_ROLES_DIR / "tasks" / "main.yml").read_text())
    assert isinstance(data, list)
    return data


def _module_key(task: dict[str, object]) -> str | None:
    for key in task:
        if key not in _TASK_KEYWORDS and key != "with_items":
            return key
    return None


def _vars() -> dict[str, Any]:
    data = yaml.safe_load((_ROLES_DIR / "vars" / "main.yml").read_text())
    assert isinstance(data, dict)
    return data


class TestDisplayManagerRoleTree:
    """S3 (spine AD-9): the role keeps the CONCERN; the template BODIES are corpus.

    The five `.j2` files moved to `dotfiles-assets` `templates/display-manager/`,
    so the role tree is tasks + vars only. Reading the bodies from the corpus here
    is deliberate: a copy in this repo would be a second source of truth.
    """

    _REQUIRED_FILES = ("tasks/main.yml", "vars/main.yml")
    _TEMPLATES = (
        "display-manager/sddm.conf.j2",
        "display-manager/config.toml.j2",
        "display-manager/regreet.toml.j2",
        "display-manager/regreet.css.j2",
        "display-manager/hypr-session.j2",
    )

    def test_role_tree_exists(self) -> None:
        for relative in self._REQUIRED_FILES:
            assert (_ROLES_DIR / relative).is_file(), f"missing {relative}"

    def test_role_no_longer_carries_a_templates_dir(self) -> None:
        assert not (_ROLES_DIR / "templates").exists(), (
            "S3 deleted the role-internal templates/ dir: the five bodies ship in the "
            "pinned corpus. Re-adding one would split a DM concern across two repos "
            "(spine AD-9)."
        )

    def test_all_five_templates_are_in_the_corpus(self) -> None:
        root = assets_templates.require_templates_root("display_manager")
        for relative in self._TEMPLATES:
            assert (root / relative).is_file(), (
                f"missing {relative} in the pinned assets templates class at {root}"
            )

    def test_playbook_exists(self) -> None:
        assert (_PLAYBOOKS_DIR / "display-manager.yaml").is_file(), (
            "missing playbooks/display-manager.yaml"
        )


class TestSddmPixieTasks:
    def test_tasks_parse_to_list_of_named_tasks(self) -> None:
        tasks = _load_tasks()
        assert tasks, "tasks/main.yml must not be empty"
        for task in tasks:
            assert isinstance(task, dict)
            assert task["name"], "every task must carry a name"

    def test_installs_sddm_packages(self) -> None:
        """The role installs sddm + Qt6 deps for the SDDM+Pixie path."""
        tasks = _load_tasks()
        pkg = next((t for t in tasks if _module_key(t) == "ansible.builtin.package"), None)
        assert pkg is not None, "missing package install task"
        module = pkg.get("ansible.builtin.package")
        assert isinstance(module, dict)
        assert module["name"] == "{{ display_manager_sddm_packages }}"

    def test_fetches_pixie_theme(self) -> None:
        """The Pixie theme (Qt6) is fetched via git into the sddm themes dir."""
        tasks = _load_tasks()
        git = next((t for t in tasks if _module_key(t) == "ansible.builtin.git"), None)
        assert git is not None, "missing Pixie theme fetch (git) task"
        module = git.get("ansible.builtin.git")
        assert isinstance(module, dict)
        assert module["dest"] == "{{ display_manager_pixie_themedir }}"

    def test_renders_sddm_config(self) -> None:
        """The role renders /etc/sddm.conf.d with the Pixie theme + Wayland
        greeter, from the pinned assets templates class (S3)."""
        tasks = _load_tasks()
        tmpl = next((t for t in tasks if "Render SDDM config" in str(t.get("name", ""))), None)
        assert tmpl is not None, "missing SDDM config render task"
        body = tmpl.get("ansible.builtin.template")
        assert isinstance(body, dict)
        assert body["dest"] == "{{ display_manager_sddm_conf }}"
        assert body["src"] == (
            "{{ display_manager_assets_templates_dir }}/display-manager/sddm.conf.j2"
        ), "the SDDM body must be read from the pinned corpus, not from the role"
        assert body.get("mode") == "0644", "assets carries no mode: the role sets it"
        assert tmpl.get("become") is True, "assets carries no privilege: the role sets it"

    def test_sddm_tasks_gated_on_type(self) -> None:
        """The SDDM+Pixie install/config tasks must gate on
        display_manager_type == 'sddm-pixie'."""
        tasks = _load_tasks()
        sddm_tasks = [
            t
            for t in tasks
            if "SDDM" in str(t.get("name", ""))
            or "Pixie" in str(t.get("name", ""))
            or "sddm config" in str(t.get("name", "")).lower()
        ]
        assert sddm_tasks, "expected SDDM+Pixie tasks"
        for t in sddm_tasks:
            assert "display_manager_type == 'sddm-pixie'" in str(t.get("when", "")), (
                f"SDDM task {t.get('name')!r} must gate on display_manager_type == sddm-pixie"
            )

    def test_enables_sddm_used_to_derive_service(self) -> None:
        data = _vars()
        assert "sddm" in str(data["display_manager_enable_service"]), (
            "default enable_service must be sddm"
        )

    def test_preflight_asserts_the_greeter_compositor(self) -> None:
        """BUG-004: DisplayServer=wayland is only viable with a Wayland
        compositor. The role must probe for weston after the package install
        and fail closed instead of letting SDDM silently degrade to x11-user
        (which starts the session on a new VT and tears it down ~90 s later)."""
        tasks = _load_tasks()
        probes = [
            task
            for task in tasks
            if _module_key(task) == "ansible.builtin.shell"
            and "command -v weston" in str(task.get("ansible.builtin.shell", ""))
        ]
        assert len(probes) == 1, (
            f"expected exactly one `command -v weston` preflight; found {len(probes)}"
        )
        probe = probes[0]
        assert probe.get("register") == "display_manager_weston_check"
        assert probe.get("changed_when") is False
        assert probe.get("failed_when") is False, "the assert must produce the failure message"
        assert "display_manager_type == 'sddm-pixie'" in str(probe.get("when"))
        assert "not ansible_check_mode" in str(probe.get("when"))

        asserts = [
            task
            for task in tasks
            if _module_key(task) == "ansible.builtin.assert"
            and "display_manager_weston_check" in str(task.get("ansible.builtin.assert"))
        ]
        assert len(asserts) == 1, "the weston probe must have a fail-closed assert"
        assertion = asserts[0]
        body = assertion["ansible.builtin.assert"]
        assert "rc" in str(body.get("that"))
        assert "display_manager_weston_check.stdout" in str(body.get("that"))
        fail_msg = str(body.get("fail_msg"))
        assert "x11-user" in fail_msg, "the failure must name the silent fallback it prevents"
        assert "BUG-004" in fail_msg
        assert "not ansible_check_mode" in str(assertion.get("when"))

    def test_login_timeout_patch_fails_closed(self) -> None:
        """The Pixie pin is a commit but the theme is third-party: the
        `interval: 5000` line must be proven present exactly once before the
        lineinfile patch. A blind lineinfile on a moved theme is a silent
        no-op, which would restore the greeter timeout."""
        tasks = _load_tasks()
        names = [str(task.get("name")) for task in tasks]
        read_name = "Read the Pixie theme login timeout source"
        assert read_name in names, "missing the pre-patch slurp of Main.qml"
        read = tasks[names.index(read_name)]
        assert _module_key(read) == "ansible.builtin.slurp"
        assert read["ansible.builtin.slurp"]["src"] == (
            "{{ display_manager_pixie_themedir }}/Main.qml"
        )
        assert read.get("become") is True
        assert "not ansible_check_mode" in str(read.get("when"))

        assert_name = "Assert the login-timeout patch matches exactly once"
        assert assert_name in names, "missing the fail-closed timeout-pattern assert"
        assertion = tasks[names.index(assert_name)]
        body = assertion["ansible.builtin.assert"]
        that = str(body.get("that"))
        assert "display_manager_pixie_main_qml.content" in that
        assert "interval: 5000" in that
        assert "| length == 1" in that, "absent OR duplicated must fail"
        fail_msg = str(body.get("fail_msg"))
        assert "exactly one" in fail_msg
        assert "BUG-004" in fail_msg
        assert assertion.get("become") is True
        assert "not ansible_check_mode" in str(assertion.get("when"))
        assert names.index(assert_name) < names.index("Fix SDDM theme login timeout"), (
            "the fail-closed assert must run BEFORE the lineinfile patch"
        )


class TestSddmConfigTemplate:
    def test_uses_pixie_theme_and_wayland_greeter(self) -> None:
        """The sddm.conf must enable the Pixie theme and a Wayland greeter (the
        no-X11-GPU-grab freeze fix). Read from the corpus: the body is an asset."""
        body = assets_templates.template_file(
            "display-manager/sddm.conf.j2", "display_manager"
        ).read_text()
        assert "Current=pixie" in body
        assert "DisplayServer={{ display_manager_sddm_display_server }}" in body
        assert "wayland" in body.lower() or "QT_QPA_PLATFORM=wayland" in body

    def test_rendered_config_names_the_weston_compositor(self) -> None:
        """BUG-004: the assets v0.6.0 body renders `[Wayland]
        CompositorCommand=<role var>`. The role supplies weston; without this
        the greeter display server cannot start and SDDM falls back to x11-user.

        Rendered with the REAL corpus body + the role's vars: a stub would not
        prove the consumer/template seam.
        """
        import jinja2

        body = assets_templates.template_file(
            "display-manager/sddm.conf.j2", "display_manager"
        ).read_text()
        data = _vars()
        rendered = jinja2.Template(body).render(
            display_manager_sddm_display_server=data["display_manager_sddm_display_server"],
            display_manager_sddm_compositor_command=data[
                "display_manager_sddm_compositor_command"
            ],
        )
        assert "DisplayServer=wayland" in rendered, "the Wayland mode must not regress to x11"
        assert "[Wayland]" in rendered
        assert "CompositorCommand=weston --shell=kiosk" in rendered
        assert "{{" not in rendered and "{%" not in rendered, "unresolved Jinja"


class TestSddmVars:
    def test_packages_include_sddm_and_qt6(self) -> None:
        data = _vars()
        pkgs = data["display_manager_sddm_packages"]
        assert "sddm" in pkgs
        assert "qt6-declarative" in pkgs
        assert "qt6-svg" in pkgs

    def test_packages_include_the_wayland_greeter_compositor(self) -> None:
        """BUG-004: SDDM's Wayland greeter is run by a compositor. weston is
        SDDM's implicit default (`weston --shell=kiosk`); leaving it out is the
        root cause of the x11-user fallback and the 90 s session bounce."""
        assert "weston" in _vars()["display_manager_sddm_packages"]

    def test_compositor_command_is_weston_kiosk(self) -> None:
        """The role supplies the `[Wayland] CompositorCommand` the assets
        v0.6.0 template renders. The template default is the same command, but
        the role must name it so the dependency is explicit and parity-tested."""
        assert _vars()["display_manager_sddm_compositor_command"] == "weston --shell=kiosk"

    def test_display_server_remains_wayland(self) -> None:
        """Do not 'fix' this by switching to x11: that reintroduces the
        X11/GPU hard-freeze the Wayland greeter exists to avoid."""
        assert _vars()["display_manager_sddm_display_server"] == "wayland"

    def test_pixie_repo_ref_is_the_tested_commit(self) -> None:
        """BUG-004: pin the theme to the commit the patch was proven against.
        `main` is a moving branch; a moved QML shape would make the login-timeout
        patch a silent no-op."""
        assert (
            _vars()["display_manager_pixie_repo_ref"]
            == "1e1a863761f742e8d509d569382b17c112e29fdc"
        )

    def test_assets_pin_is_v060(self) -> None:
        """The `[Wayland] CompositorCommand` body ships in assets v0.6.0
        (req-006); v0.5.0 has no [Wayland] section at all."""
        assert _vars()["display_manager_assets_pinned_tag"] == "v0.6.0"

    def test_pixie_repo_and_theme_dir(self) -> None:
        data = _vars()
        assert "github.com/xCaptaiN09/pixie-sddm" in str(data["display_manager_pixie_repo"])
        assert "pixie" in str(data["display_manager_pixie_themedir"])

    def test_default_type_is_sddm_pixie(self) -> None:
        data = _vars()
        assert data["display_manager_type"] == "sddm-pixie"

    def test_disables_greetd_and_lightdm(self) -> None:
        data = _vars()
        assert "greetd" in data["display_manager_disable_services"]
        assert "lightdm" in data["display_manager_disable_services"]


class TestGreetdFallbackRetained:
    def test_greetd_regreet_config_still_rendered(self) -> None:
        """The greetd+regreet files remain (in the corpus) so a user can fall back
        by setting display_manager_type == 'greetd-regreet'."""
        assert assets_templates.template_file(
            "display-manager/config.toml.j2", "display_manager"
        ).is_file()
        greetd = next(
            (t for t in _load_tasks() if "Render greetd config" in str(t.get("name", ""))), None
        )
        assert greetd is not None, "missing greetd config render task"
        body = greetd.get("ansible.builtin.template")
        assert isinstance(body, dict)
        assert body["src"] == (
            "{{ display_manager_assets_templates_dir }}/display-manager/config.toml.j2"
        )
        for t in _load_tasks():
            if "greetd" in str(t.get("name", "")).lower():
                assert "display_manager_type == 'greetd-regreet'" in str(t.get("when", "")), (
                    f"greetd task {t.get('name')!r} must gate on greetd-regreet type"
                )

    def test_hypr_session_wrapper_retained_in_the_corpus(self) -> None:
        assert assets_templates.template_file(
            "display-manager/hypr-session.j2", "display_manager"
        ).is_file()

    def test_unrendered_fallback_bodies_are_still_assets(self) -> None:
        """regreet.toml/css and hypr-session have no render task at this tag, but
        their bodies and contracts are corpus files (spine AD-9) — not role files
        and not rendered output."""
        root = assets_templates.require_templates_root("display_manager")
        for relative in (
            "display-manager/regreet.toml.j2",
            "display-manager/regreet.css.j2",
            "display-manager/hypr-session.j2",
        ):
            assert (root / relative).is_file(), f"missing {relative}"


class TestDisplayManagerPlaybook:
    def test_syntax_check_exits_zero(self) -> None:
        ansible_playbook = shutil.which("ansible-playbook")
        if ansible_playbook is None:
            pytest.skip("ansible-playbook not installed; skipping syntax-check")
        env = {k: v for k, v in __import__("os").environ.items() if not k.startswith("ANSIBLE_")}
        env["ANSIBLE_CONFIG"] = str(_ANSIBLE_DIR / "ansible.cfg")
        result = subprocess.run(
            [ansible_playbook, "--syntax-check", str(_PLAYBOOKS_DIR / "display-manager.yaml")],
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
