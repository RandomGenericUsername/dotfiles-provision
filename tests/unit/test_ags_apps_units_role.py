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
_ASSETS_AUTOSTART = _FIXTURES / "autostart" / "v0.6.2.lua"

_SEVEN_APPS = [
    "bar",
    "notifications",
    "capture",
    "clipboard",
    "wallpaper-selector",
    "icme",
    "btop-theme-studio",
]


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

        # dotfiles-assets v0.6.2 owns the autostart content: the always-on bar
        # and notifications overlay plus the boot-staggered capture and
        # clipboard overlays. The on-demand selector/icme/studio do not appear.
        assert apps["bar"]["autostart"] == "ags"
        assert apps["notifications"]["autostart"] == "notifications"
        assert apps["capture"]["autostart"] == "capture"
        assert apps["clipboard"]["autostart"] == "clipboard"
        for app in ("wallpaper-selector", "icme", "btop-theme-studio"):
            assert "autostart" not in apps[app]

    def test_assets_v062_autostart_starts_each_declared_identity_once(self) -> None:
        content = _ASSETS_AUTOSTART.read_text()
        for entry in _app_list():
            if "autostart" not in entry:
                continue
            identity = entry["autostart"]
            assert content.count(f"--expect-instance {identity}") == 1, identity
            assert "ags-run-locked" in content
        # No on-demand app is started at login.
        for app in ("wallpaper-selector", "icme", "btop-theme-studio"):
            assert f"--expect-instance {app}" not in content


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
        assert imports.index("ags-apps-units.yaml") < imports.index("compositor-configs.yaml")

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
        assert "v0.5.0" not in vars_text
        assert "v0.3.0" not in vars_text
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
                    assert module.get("state") == "absent" and dest.endswith(".git"), (
                        f"task {task.get('name')!r} mutates the immutable tag"
                    )

    def test_colors_and_icons_are_verified_not_produced(self) -> None:
        verify_unit = (_ROLE / "tasks" / "_verify_unit.yml").read_text()
        assert "colors.css" in verify_unit
        assert "runtime_colors_pointer" in verify_unit
        assert "icons.json" in verify_unit
        assert "checksum" in verify_unit
        assert "ansible.builtin.copy" not in verify_unit
        assert "ansible.builtin.template" not in verify_unit

    def test_installer_verifies_the_autostart_surface_under_the_shared_lock(self) -> None:
        surfaces = (_ROLE / "tasks" / "_verify_surfaces.yml").read_text()
        assert "app.autostart" in surfaces
        assert "--expect-instance " in surfaces
        assert "ags-run-locked" in surfaces
        assert "| length - 1) == 1" in surfaces, (
            "the autostart identity must appear exactly once (no duplicate process)"
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

    def test_verify_mirror_requires_the_autostart_surface_under_the_shared_lock(
        self,
    ) -> None:
        verify_one = (_ROLES_DIR / "verify" / "tasks" / "_verify_standalone.yml").read_text()
        assert "app.autostart" in verify_one
        assert "--expect-instance " in verify_one
        assert "ags-run-locked" in verify_one
        assert "| length - 1) == 1" in verify_one

    def test_verify_mirror_covers_all_standalone_surfaces(self) -> None:
        verify_tasks = (_ROLES_DIR / "verify" / "tasks" / "main.yml").read_text()
        assert "_verify_standalone.yml" in verify_tasks
        verify_one = (_ROLES_DIR / "verify" / "tasks" / "_verify_standalone.yml").read_text()
        for needle in (
            "app.installDir",
            "app.tag",
            "verify_ags_apps_units_platform_shortcut",
            "colors.css",
            "icons.json",
            "autostart",
            "ags-run-locked",
        ):
            assert needle in verify_one, f"verify mirror misses {needle!r}"


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
    if [ "${argv[0]:-}" = "palette-refresh" ]; then
      echo '{"ok":true}'
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
    subprocess.run(["git", "-C", str(repo), "tag", "v0.1.0"], check=True)
    return repo


def _write_composition(
    root: Path,
    repos: dict[str, Path],
    *,
    tags: dict[str, str] | None = None,
    fixture: str = "all-standalone.apps.yaml",
) -> Path:
    """Write the composition app list with per-test repo/tag overrides."""
    provisioning = root / "composition" / "dotfiles" / "provisioning"
    provisioning.mkdir(parents=True, exist_ok=True)
    document = yaml.safe_load((_APP_LISTS / fixture).read_text(encoding="utf-8"))
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
        "schemaVersion: 1\nags-platform: v0.3.0\ncontracts: v0.3.0\ndotfiles-assets: v0.6.2\n",
        encoding="utf-8",
    )
    return provisioning


def _stage_fake_platform(install: Path, icons_json: str = '{"schemaVersion": 1}\n') -> Path:
    unit = install / "ags-platform" / "v0.3.0"
    unit.mkdir(parents=True)
    (unit / "index.ts").write_text("", encoding="utf-8")
    (unit / "icons.json").write_text(icons_json, encoding="utf-8")
    return unit


def _stage_autostart(install: Path) -> Path:
    """Install the verbatim assets v0.6.2 autostart fixture (never written by a role)."""
    path = install / "config" / "hypr" / "autostart.lua"
    path.parent.mkdir(parents=True)
    path.write_text(_ASSETS_AUTOSTART.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def _run_role(
    tmp_path: Path,
    provisioning: Path,
    *,
    cutover: bool = False,
    check: bool = False,
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
        ANSIBLE_CONFIG=str(_ANSIBLE_DIR / "ansible.cfg"),
        PATH=f"{bin_dir}:{os.environ.get('PATH', '')}",
    )
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
        "registry": str(registry),
        "home": str(home),
    }


def _stage_seven_app_repos(tmp_path: Path) -> tuple[dict[str, Path], Path]:
    """Build the seven fake app repos and the runtime palette pointer."""
    colors = tmp_path / "state" / "dotfiles" / "current" / "colors.gtk.css"
    colors.parent.mkdir(parents=True)
    colors.write_text("@define-color color_background #0b0b1a;\n", encoding="utf-8")
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
            colors_pointer=colors if entry.get("barPalettePointer") else None,
            icons_json=icons_json if app_id == "bar" else None,
        )
    return repos, icons or ""


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
                unit = install / "apps" / entry["installDir"] / "v0.1.0"
                spine = install / "config" / entry["spineLink"]
                xdg = Path(paths["xdg"]) / entry["xdgLink"]
                assert (unit / "app.tsx").is_file(), app_id
                assert not (unit / ".git").exists(), app_id
                assert (install / "apps" / entry["installDir"] / "pinned").read_text().strip() == "v0.1.0"
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
            assert os.readlink(shortcut) == str(install / "ags-platform" / "v0.3.0")

            assert os.readlink(install / "config" / "ags") == str(
                install / "apps" / "bar" / "v0.1.0"
            )
            bar_unit = install / "apps" / "bar" / "v0.1.0"
            assert (bar_unit / "colors.css").is_symlink()
            assert os.readlink(bar_unit / "colors.css") == str(
                Path(paths["state"]) / "dotfiles" / "current" / "colors.gtk.css"
            )
            assert (bar_unit / "icons.json").read_bytes() == bar_icons.encode()

            # Always-on apps remain on the bus; every on-demand app was started
            # for the cutover proof and stopped again.
            assert sorted(Path(paths["registry"]).read_text().splitlines()) == [
                "ags",
                "notifications",
            ]
            # No legacy monorepo surface was created by any role.
            assert not (install / "ags-apps").exists()
            assert not (install / "config" / "ags-hypr-pano").exists()
            assert not (Path(paths["bin"]) / "hypr-pano-ui").exists()
        finally:
            _stop_fake_ags(paths)

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
                install / "apps" / entry["installDir"] / "v0.1.0"
                for entry in _app_list()
            ]
            before = {str(path): _sha256_tree(path) for path in units}
            second, _ = _run_role(tmp_path, provisioning, cutover=True)
            assert second.returncode == 0, second.stdout + second.stderr
            after = {str(path): _sha256_tree(path) for path in units}
            assert before == after
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
        subprocess.run(["git", "-C", str(capture), "tag", "-f", "v0.1.0"], check=True)
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
            colors = (
                Path(paths["state"]) / "dotfiles" / "current" / "colors.gtk.css"
            )
            state_before = colors.read_text()
            old_units = [
                install / "apps" / entry["installDir"] / "v0.1.0"
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
            assert colors.read_text() == state_before
        finally:
            _stop_fake_ags(paths)


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
