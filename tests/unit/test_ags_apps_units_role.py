"""REQ-008: generic per-app AGS install topology and one-owner cutover.

The role reads the composition's `apps.yaml` + `program-tuple.yaml` and acts
only on `owner: standalone`. These tests pin the structure (owner filters,
immutable-tag discipline, tuple shortcut, quiesce->repoint->start->verify
ordering, rollback, launch lock) and execute the role against local fake app
repos with a fake AGS CLI — GUI-free, no network, no real cutover.
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


def _named(name: str) -> dict[str, Any]:
    task = next((item for item in _all_tasks() if item.get("name") == name), None)
    assert task is not None, f"missing task {name!r}"
    return task


def _app_list(name: str) -> list[dict[str, Any]]:
    data = yaml.safe_load((_APP_LISTS / name).read_text())
    assert isinstance(data, dict)
    return list(data["apps"])


class TestOwnerFilters:
    @pytest.mark.parametrize(
        ("fixture", "legacy", "standalone"),
        [
            ("legacy.apps.yaml", 2, 0),
            ("mixed.apps.yaml", 1, 1),
            ("all-standalone.apps.yaml", 0, 2),
            ("clipboard.apps.yaml", 1, 1),
        ],
    )
    def test_every_fixture_has_exactly_one_owner(
        self, fixture: str, legacy: int, standalone: int
    ) -> None:
        apps = _app_list(fixture)
        legacy_apps = [entry for entry in apps if entry["owner"] == "legacy"]
        standalone_apps = [entry for entry in apps if entry["owner"] == "standalone"]
        assert len(legacy_apps) == legacy
        assert len(standalone_apps) == standalone
        assert {entry["app"] for entry in legacy_apps}.isdisjoint(
            {entry["app"] for entry in standalone_apps}
        )
        assert len(legacy_apps) + len(standalone_apps) == len(apps)

    def test_role_reads_the_single_app_list_and_tuple(self) -> None:
        vars_text = (_ROLE / "vars" / "main.yml").read_text()
        assert "manifests_dir" in vars_text
        assert "apps.yaml" in vars_text
        assert "program-tuple.yaml" in vars_text
        assert "owner', 'equalto', 'standalone'" in (_ROLE / "tasks" / "main.yml").read_text()

    def test_old_role_filters_legacy_owner_and_keeps_its_pin(self) -> None:
        old_vars = yaml.safe_load((_ROLES_DIR / "ags_apps" / "vars" / "main.yml").read_text())
        assert old_vars["ags_apps_version"] == "v0.5.0"
        old_tasks = (_ROLES_DIR / "ags_apps" / "tasks" / "main.yml").read_text()
        assert "apps.yaml" in old_tasks
        assert "selectattr('owner', 'equalto', 'legacy')" in old_tasks
        assert "ags_apps_legacy_names" in old_tasks


class TestClipboardCutoverContract:
    """The clipboard pilot is the first real per-app cutover.

    The engine has to be ready for the composition flip without flipping it:
    the app-list shape is `clipboard`/`ags-clipboard`/`clipboard-ui`, and every
    legacy role keys off that same name so an `owner: standalone` entry is left
    entirely to `ags_apps_units`.
    """

    def test_clipboard_fixture_names_the_exact_standalone_surfaces(self) -> None:
        apps = {entry["app"]: entry for entry in _app_list("clipboard.apps.yaml")}
        assert apps["bar"]["owner"] == "legacy"
        clipboard = apps["clipboard"]
        assert clipboard["owner"] == "standalone"
        assert clipboard["installDir"] == "clipboard"
        assert clipboard["instance"] == "clipboard"
        assert clipboard["configDir"] == "ags-clipboard"
        assert clipboard["configLink"] == "ags-clipboard"
        assert clipboard["spineLink"] == "ags-clipboard"
        assert clipboard["xdgLink"] == "ags-clipboard"
        assert clipboard["launcher"] == "clipboard-ui"
        assert clipboard["autostart"] == "clipboard"
        assert clipboard["launch"] == "on-demand"

    def test_legacy_roles_key_on_clipboard_so_standalone_skips(self) -> None:
        cli_tasks = (_ROLES_DIR / "cli_tools" / "tasks" / "main.yml").read_text()
        assert 'src: clipboard-ui.j2' in cli_tasks
        assert '"{{ cli_tools_bin_dir }}/clipboard-ui"' in cli_tasks
        assert "when: \"'clipboard' in cli_tools_legacy_app_names\"" in cli_tasks
        assert "hypr-pano-ui" not in cli_tasks

        config_vars = (_ROLES_DIR / "config_links" / "vars" / "main.yml").read_text()
        assert "ags-clipboard" in config_vars
        assert "ags-hypr-pano" not in config_vars
        config_tasks = (_ROLES_DIR / "config_links" / "tasks" / "main.yml").read_text()
        assert "selectattr('owner', 'equalto', 'standalone')" in config_tasks
        assert "map(attribute='xdgLink')" in config_tasks

        gui_vars = (_ROLES_DIR / "gui_tools" / "vars" / "main.yml").read_text()
        assert "  - name: clipboard\n    always_on: false" in gui_vars
        assert "  - name: hypr-pano\n" not in gui_vars

        # The old monorepo role remains the legacy owner of hypr-pano (the
        # v0.5.0 unit still ships that directory), so its live-pano link stays
        # gated on the OLD app id. Once the composition list says `clipboard`,
        # no legacy name matches and the old role creates no pano link.
        old_tasks = (_ROLES_DIR / "ags_apps" / "tasks" / "main.yml").read_text()
        assert "when: \"'hypr-pano' in ags_apps_legacy_names\"" in old_tasks
        assert "'clipboard' in ags_apps_legacy_names" not in old_tasks


class TestRoleStructure:
    def test_role_and_playbook_exist(self) -> None:
        assert (_ROLE / "tasks" / "main.yml").is_file()
        assert (_ROLE / "vars" / "main.yml").is_file()
        assert (_ANSIBLE_DIR / "playbooks" / "ags-apps-units.yaml").is_file()

    def test_bootstrap_imports_the_generic_role_after_the_legacy_role(self) -> None:
        imports = [
            str(entry["import_playbook"])
            for entry in yaml.safe_load((_ANSIBLE_DIR / "playbooks" / "bootstrap.yaml").read_text())
        ]
        assert imports.index("ags-apps.yaml") < imports.index("ags-apps-units.yaml")
        assert imports.index("ags-apps-units.yaml") < imports.index("compositor-configs.yaml")

    def test_install_path_and_shared_shortcut_match_ad31(self) -> None:
        vars_text = (_ROLE / "vars" / "main.yml").read_text()
        assert "install_dir | trim }}/apps" in vars_text
        assert "app.installDir" in vars_text
        assert "app.tag" in vars_text
        assert "node_modules" in vars_text
        assert "ags_apps_units_platform_shortcut" in vars_text
        assert "ags_apps_units_tuple['ags-platform']" in vars_text

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

    def test_verify_mirror_requires_the_autostart_surface_under_the_shared_lock(
        self,
    ) -> None:
        verify_one = (_ROLES_DIR / "verify" / "tasks" / "_verify_standalone.yml").read_text()
        assert "app.autostart" in verify_one
        assert "--expect-instance " in verify_one
        assert "ags-run-locked" in verify_one
        assert "| length - 1) == 1" in verify_one

    def test_role_consumes_the_program_tuple_not_a_second_pin(self) -> None:
        vars_text = (_ROLE / "vars" / "main.yml").read_text()
        assert "program-tuple.yaml" in vars_text
        assert "ags_apps_units_tuple['ags-platform']" in vars_text
        assert "v0.5.0" not in vars_text
        assert "v0.3.0" not in vars_text


class TestVerifyMirror:
    def test_verify_role_mirrors_the_generic_topology(self) -> None:
        verify_tasks = (_ROLES_DIR / "verify" / "tasks" / "main.yml").read_text()
        assert "_verify_standalone.yml" in verify_tasks
        assert "verify_ags_standalone_apps" in verify_tasks
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
        verify_vars = (_ROLES_DIR / "verify" / "vars" / "main.yml").read_text()
        assert "verify_ags_apps_units_apps_file" in verify_vars
        assert "ags-run-locked" in verify_vars


class TestLaunchLockWiring:
    def test_shared_wrapper_is_installed_by_cli_tools(self) -> None:
        tasks = (_ROLES_DIR / "cli_tools" / "tasks" / "main.yml").read_text()
        assert "ags-run-locked" in tasks
        wrapper = _ROLES_DIR / "cli_tools" / "files" / "ags-run-locked"
        assert wrapper.is_file()
        assert os.access(wrapper, os.X_OK)

    def test_every_provisioned_launcher_uses_the_wrapper(self) -> None:
        templates = _ROLES_DIR / "cli_tools" / "templates"
        for name in (
            "capture-ui.j2",
            "clipboard-ui.j2",
            "wallpaper-selector-ui.j2",
            "icon-color-mapping-editor.j2",
            "btop-theme-studio.j2",
        ):
            text = (templates / name).read_text()
            assert "ags-run-locked" in text, f"{name} bypasses the launch lock"
            executable = "\n".join(
                line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")
            )
            assert "exec ags run" not in executable
            assert "ags run -d" not in executable
        generic = (_ROLE / "templates" / "ags-app-launcher.j2").read_text()
        assert "ags-run-locked" in generic
        assert "exec ags run" not in generic

    def test_gui_tools_start_paths_and_instance_filter_use_the_owner_list(self) -> None:
        tasks = (_ROLES_DIR / "gui_tools" / "tasks" / "main.yml").read_text()
        assert "apps.yaml" in tasks
        assert "gui_tools_ags_active_instances" in tasks
        assert "gui_tools_ags_always_on_active_instances" in tasks
        variables = (_ROLES_DIR / "gui_tools" / "vars" / "main.yml").read_text()
        assert "ags-run-locked --expect-instance ags" in variables
        assert "ags-run-locked --expect-instance notifications" in variables
        assert 'launch: "ags run"' not in variables


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
mkdir -p "$(dirname "$REG")"
touch "$REG"
case "$1" in
  list) cat "$REG" ;;
  quit)
    shift
    name=""
    while [ "$#" -gt 0 ]; do
      case "$1" in -i) name="$2"; shift 2 ;; *) shift ;; esac
    done
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
    echo "$name" >> "$REG"
    echo "$$" > "$REG.$name.pid"
    trap 'grep -vx "$name" "$REG" > "$REG.tmp" 2>/dev/null || true; mv "$REG.tmp" "$REG"; rm -f "$REG.$name.pid"; exit 0' TERM INT
    sleep "${FAKE_AGS_RUN_SECONDS:-60}" &
    wait $!
    ;;
  request)
    if [ "${2:-}" = "palette-refresh" ]; then
      echo '{"ok":true}'
      exit 0
    fi
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
    colors_pointer: Path | None = None,
    include_bin_tool: bool = True,
    icons_json: str | None = None,
) -> Path:
    app = app or name
    instance = instance or name
    config_dir = config_dir or f"ags-{name}"
    repo = root / "repos" / name
    shutil.copytree(_FAKE_APP, repo)
    if not include_bin_tool:
        (repo / "bin" / "fake-app-tool").unlink()
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
    fixture: str,
    repos: dict[str, Path],
    *,
    tags: dict[str, str] | None = None,
    owners: dict[str, str] | None = None,
) -> Path:
    """Write the composition app list with per-test repo/tag/owner overrides."""
    provisioning = root / "composition" / "dotfiles" / "provisioning"
    provisioning.mkdir(parents=True, exist_ok=True)
    document = yaml.safe_load((_APP_LISTS / fixture).read_text(encoding="utf-8"))
    tags = tags or {}
    owners = owners or {}
    for entry in document["apps"]:
        app_id = entry["app"]
        if app_id in owners:
            entry["owner"] = owners[app_id]
            if owners[app_id] == "legacy":
                entry.pop("repo", None)
                entry.pop("tag", None)
        if app_id in repos and entry["owner"] == "standalone":
            entry["repo"] = str(repos[app_id])
        if app_id in tags and entry["owner"] == "standalone":
            entry["tag"] = tags[app_id]
    (provisioning / "apps.yaml").write_text(
        yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
    )
    (provisioning / "program-tuple.yaml").write_text(
        "schemaVersion: 1\nags-platform: v0.3.0\ncontracts: v0.3.0\ndotfiles-assets: v0.6.1\n",
        encoding="utf-8",
    )
    return provisioning


def _stage_fake_platform(install: Path, icons_json: str = '{"schemaVersion": 1}\n') -> Path:
    unit = install / "ags-platform" / "v0.3.0"
    unit.mkdir(parents=True)
    (unit / "index.ts").write_text("", encoding="utf-8")
    (unit / "icons.json").write_text(icons_json, encoding="utf-8")
    return unit


def _stage_autostart(install: Path, entries: list[dict[str, Any]]) -> Path:
    """Write the assets-owned autostart file the role verifies (never writes)."""
    path = install / "config" / "hypr" / "autostart.lua"
    path.parent.mkdir(parents=True)
    lines = ['hl.on("hyprland.start", function()']
    for entry in entries:
        if "autostart" not in entry:
            continue
        lines.append(
            '    hl.exec_cmd("ags-run-locked --expect-instance '
            f'{entry["autostart"]} -d $HOME/.config/{entry["xdgLink"]}")'
        )
    lines.append("end)")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
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
    result = subprocess.run(args, capture_output=True, text=True, env=env, timeout=180)
    return result, {
        "install": str(install),
        "xdg": str(xdg),
        "bin": str(bin_dir),
        "state": str(state),
        "registry": str(registry),
        "home": str(home),
    }


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
    def test_legacy_list_is_a_complete_noop(self, tmp_path: Path) -> None:
        provisioning = _write_composition(tmp_path, "legacy.apps.yaml", {})
        result, paths = _run_role(tmp_path, provisioning)
        try:
            assert result.returncode == 0, result.stdout + result.stderr
            assert "is dormant" in result.stdout
            assert not Path(paths["install"]).exists(), (
                "the generic role must not create <install>/apps for an all-legacy list"
            )
        finally:
            _stop_fake_ags(paths)

    def test_mixed_list_installs_only_the_standalone_owner(self, tmp_path: Path) -> None:
        repo = _make_app_repo(tmp_path, "fake-app", config_dir="ags-fake-app")
        provisioning = _write_composition(tmp_path, "mixed.apps.yaml", {"fake-app": repo})
        _stage_fake_platform(tmp_path / "install")
        _stage_autostart(tmp_path / "install", _app_list("mixed.apps.yaml"))
        result, paths = _run_role(tmp_path, provisioning)
        install = Path(paths["install"])
        try:
            assert result.returncode == 0, result.stdout + result.stderr
            assert (install / "apps" / "fake-app" / "v0.1.0" / "app.tsx").is_file()
            assert not (install / "apps" / "bar").exists(), (
                "a legacy entry must not be installed by the standalone role"
            )
            assert (install / "apps" / "fake-app" / "pinned").read_text().strip() == "v0.1.0"
            assert (install / "config" / "ags-fake-app").is_symlink()
            assert (Path(paths["xdg"]) / "ags-fake-app").is_symlink()
            assert (Path(paths["bin"]) / "fake-app-ui").is_file()
            assert Path(paths["registry"]).read_text().splitlines() == ["fake-app"]
        finally:
            _stop_fake_ags(paths)

    def test_clipboard_cutover_installs_the_standalone_topology_and_surfaces(
        self, tmp_path: Path
    ) -> None:
        """The clipboard pilot is the first real cutover: one list flip must
        install `<install>/apps/clipboard/<tag>`, create the
        config/spine/XDG surfaces `ags-clipboard`, render `clipboard-ui`
        through the shared launch lock with the clipboard instance/log, and
        verify the assets-owned `clipboard` autostart identity exactly once.
        The old monorepo surfaces (`ags-hypr-pano`, `hypr-pano-ui`) must not be
        created by the standalone role."""
        install = tmp_path / "install"
        repo = _make_app_repo(
            tmp_path,
            "clipboard",
            app="clipboard",
            instance="clipboard",
            config_dir="ags-clipboard",
        )
        provisioning = _write_composition(
            tmp_path, "clipboard.apps.yaml", {"clipboard": repo}
        )
        _stage_fake_platform(install)
        _stage_autostart(install, _app_list("clipboard.apps.yaml"))
        result, paths = _run_role(tmp_path, provisioning, cutover=True)
        try:
            assert result.returncode == 0, result.stdout + result.stderr
            unit = install / "apps" / "clipboard" / "v0.1.0"
            spine_link = install / "config" / "ags-clipboard"
            xdg_link = Path(paths["xdg"]) / "ags-clipboard"
            launcher = Path(paths["bin"]) / "clipboard-ui"
            assert (unit / "app.tsx").is_file()
            assert (install / "apps" / "clipboard" / "pinned").read_text().strip() == "v0.1.0"
            assert spine_link.is_symlink() and os.readlink(spine_link) == str(unit)
            assert xdg_link.is_symlink() and os.readlink(xdg_link) == str(spine_link)
            assert launcher.is_file()
            text = launcher.read_text()
            assert 'INSTANCE="clipboard"' in text
            assert 'DIR="' + str(Path(paths["xdg"]) / "ags-clipboard") + '"' in text
            assert 'LOG="' + str(Path(paths["state"]) / "ags" / "clipboard.log") + '"' in text
            assert "ags-run-locked" in text
            assert "--expect-instance" in text
            assert "clipboard" in text
            assert not (install / "config" / "ags-hypr-pano").exists(), (
                "the standalone role must not create the retired pano link"
            )
            assert not (Path(paths["bin"]) / "hypr-pano-ui").exists(), (
                "the standalone role must not create the retired pano launcher"
            )
            assert Path(paths["registry"]).read_text().splitlines() == [], (
                "the on-demand clipboard instance is stopped after cutover proof"
            )
        finally:
            _stop_fake_ags(paths)

    def test_all_standalone_installs_full_topology_and_tags_stay_immutable(
        self, tmp_path: Path
    ) -> None:
        install = tmp_path / "install"
        state = tmp_path / "state"
        colors = state / "dotfiles" / "current" / "colors.gtk.css"
        colors.parent.mkdir(parents=True)
        colors.write_text("", encoding="utf-8")
        bar = _make_app_repo(
            tmp_path,
            "bar",
            app="bar",
            instance="ags",
            config_dir="ags",
            colors_pointer=colors,
        )
        app = _make_app_repo(tmp_path, "fake-app", config_dir="ags-fake-app")
        provisioning = _write_composition(
            tmp_path, "all-standalone.apps.yaml", {"bar": bar, "fake-app": app}
        )
        _stage_fake_platform(install, icons_json=(app / "icons.json").read_text())
        _stage_autostart(install, _app_list("all-standalone.apps.yaml"))
        result, paths = _run_role(tmp_path, provisioning, cutover=True)
        try:
            assert result.returncode == 0, result.stdout + result.stderr
            unit = install / "apps" / "fake-app" / "v0.1.0"
            bar_unit = install / "apps" / "bar" / "v0.1.0"
            shortcut = install / "apps" / "node_modules" / "ags-platform"
            assert shortcut.is_symlink()
            assert os.readlink(shortcut) == str(install / "ags-platform" / "v0.3.0")
            assert (install / "config" / "ags").is_symlink()
            assert os.readlink(install / "config" / "ags") == str(bar_unit)
            assert Path(paths["xdg"]) / "ags-fake-app" / "app.tsx"
            assert (Path(paths["bin"]) / "fake-app-tool").is_symlink()
            launcher = Path(paths["bin"]) / "fake-app-ui"
            assert "ags-run-locked" in launcher.read_text()
            assert (bar_unit / "colors.css").is_symlink()
            assert os.readlink(bar_unit / "colors.css") == str(colors)
            assert not (unit / ".git").exists()
            assert not (bar_unit / ".git").exists()
            # The on-demand app was started for the epoch, verified, then
            # stopped; the always-on bar remains on the bus.
            assert Path(paths["registry"]).read_text().splitlines() == ["ags"]

            before = {str(path): _sha256_tree(path) for path in (unit, bar_unit)}
            second, _paths2 = _run_role(tmp_path, provisioning, cutover=True)
            assert second.returncode == 0, second.stdout + second.stderr
            after = {str(path): _sha256_tree(path) for path in (unit, bar_unit)}
            assert before == after, "a re-provision must not write inside installed tags"
        finally:
            _stop_fake_ags(paths)

    def test_failure_rolls_back_links_and_restarts_the_previous_instance(
        self, tmp_path: Path
    ) -> None:
        install = tmp_path / "install"
        xdg = tmp_path / "xdg"
        old_dir = tmp_path / "old-fake-app"
        old_dir.mkdir()
        (old_dir / "app.manifest.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "app": "fake-app",
                    "instance": "fake-app",
                    "configDir": "ags-fake-app",
                    "mode": "live",
                    "holdsUnsavedState": False,
                }
            ),
            encoding="utf-8",
        )
        install.mkdir()
        xdg.mkdir()
        (install / "config").mkdir()
        (install / "config" / "ags-fake-app").symlink_to(old_dir)
        (xdg / "ags-fake-app").symlink_to(install / "config" / "ags-fake-app")
        (tmp_path / "fake-ags-registry").write_text("fake-app\n", encoding="utf-8")
        _stage_fake_platform(install)
        _stage_autostart(install, _app_list("mixed.apps.yaml"))
        # The repo omits its declared bin entry, so the post-repoint surface
        # assertion fails and the rollback block must restore the old links.
        repo = _make_app_repo(
            tmp_path, "fake-app", config_dir="ags-fake-app", include_bin_tool=False
        )
        provisioning = _write_composition(tmp_path, "mixed.apps.yaml", {"fake-app": repo})
        result, paths = _run_role(tmp_path, provisioning)
        registry = Path(paths["registry"])
        try:
            assert result.returncode != 0
            assert "rollback restored" in result.stdout.lower()
            assert os.readlink(install / "config" / "ags-fake-app") == str(old_dir)
            assert os.readlink(xdg / "ags-fake-app") == str(install / "config" / "ags-fake-app")
            assert registry.read_text().splitlines() == ["fake-app"]
        finally:
            _stop_fake_ags(paths)

    def test_owner_flip_quiesces_the_old_instance_then_installs_and_starts(
        self, tmp_path: Path
    ) -> None:
        """AD-32: the composition flip is the only ownership change. Before the
        flip the generic role is dormant; after it, the role quiesces the old
        instance, installs the tag, repoints the links and starts/verifies."""
        install = tmp_path / "install"
        xdg = tmp_path / "xdg"
        old_dir = tmp_path / "old-fake-app"
        old_dir.mkdir()
        (old_dir / "app.manifest.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "app": "fake-app",
                    "instance": "fake-app",
                    "configDir": "ags-fake-app",
                    "mode": "live",
                    "holdsUnsavedState": False,
                }
            ),
            encoding="utf-8",
        )
        install.mkdir()
        xdg.mkdir()
        (install / "config").mkdir()
        (install / "config" / "ags-fake-app").symlink_to(old_dir)
        (xdg / "ags-fake-app").symlink_to(install / "config" / "ags-fake-app")
        (tmp_path / "fake-ags-registry").write_text("fake-app\n", encoding="utf-8")
        _stage_fake_platform(install)
        _stage_autostart(install, _app_list("mixed.apps.yaml"))
        repo = _make_app_repo(tmp_path, "fake-app", config_dir="ags-fake-app")

        before_path = _write_composition(
            tmp_path,
            "mixed.apps.yaml",
            {"fake-app": repo},
            owners={"fake-app": "legacy"},
        )
        before, paths = _run_role(tmp_path, before_path, cutover=True)
        try:
            assert before.returncode == 0, before.stdout + before.stderr
            assert "is dormant" in before.stdout
            assert os.readlink(install / "config" / "ags-fake-app") == str(old_dir)
            assert Path(paths["registry"]).read_text().splitlines() == ["fake-app"]

            after_path = _write_composition(
                tmp_path, "mixed.apps.yaml", {"fake-app": repo}
            )
            after, paths = _run_role(tmp_path, after_path, cutover=True)
            assert after.returncode == 0, after.stdout + after.stderr
            unit = install / "apps" / "fake-app" / "v0.1.0"
            assert os.readlink(install / "config" / "ags-fake-app") == str(unit)
            assert os.readlink(xdg / "ags-fake-app") == str(
                install / "config" / "ags-fake-app"
            )
            assert Path(paths["registry"]).read_text().splitlines() == ["fake-app"]
        finally:
            _stop_fake_ags(paths)

    def test_tag_bump_repoints_links_and_preserves_external_state(
        self, tmp_path: Path
    ) -> None:
        """AD-37: a tag bump installs a NEW immutable tree, repoints the links
        and leaves the previous tag plus the runtime-owned state unchanged."""
        install = tmp_path / "install"
        state = tmp_path / "state"
        colors = state / "dotfiles" / "current" / "colors.gtk.css"
        colors.parent.mkdir(parents=True)
        colors.write_text("@define-color color_background #0b0b1a;\n", encoding="utf-8")
        bar = _make_app_repo(
            tmp_path,
            "bar",
            app="bar",
            instance="ags",
            config_dir="ags",
            colors_pointer=colors,
        )
        app = _make_app_repo(tmp_path, "fake-app", config_dir="ags-fake-app")
        provisioning = _write_composition(
            tmp_path, "all-standalone.apps.yaml", {"bar": bar, "fake-app": app}
        )
        _stage_fake_platform(install, icons_json=(app / "icons.json").read_text())
        _stage_autostart(install, _app_list("all-standalone.apps.yaml"))
        first, paths = _run_role(tmp_path, provisioning, cutover=True)
        try:
            assert first.returncode == 0, first.stdout + first.stderr
            old_app_unit = install / "apps" / "fake-app" / "v0.1.0"
            old_bar_unit = install / "apps" / "bar" / "v0.1.0"
            before = {str(path): _sha256_tree(path) for path in (old_app_unit, old_bar_unit)}
            state_before = colors.read_text()

            for repo in (bar, app):
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
                tmp_path,
                "all-standalone.apps.yaml",
                {"bar": bar, "fake-app": app},
                tags={"bar": "v0.2.0", "fake-app": "v0.2.0"},
            )
            second, paths = _run_role(tmp_path, bumped, cutover=True)
            assert second.returncode == 0, second.stdout + second.stderr
            new_app_unit = install / "apps" / "fake-app" / "v0.2.0"
            new_bar_unit = install / "apps" / "bar" / "v0.2.0"
            assert (new_app_unit / "app.tsx").is_file()
            assert (install / "apps" / "fake-app" / "pinned").read_text().strip() == "v0.2.0"
            assert os.readlink(install / "config" / "ags") == str(new_bar_unit)
            assert os.readlink(install / "config" / "ags-fake-app") == str(new_app_unit)
            assert os.readlink(new_bar_unit / "colors.css") == str(colors)
            after = {str(path): _sha256_tree(path) for path in (old_app_unit, old_bar_unit)}
            assert before == after, "a tag bump must not mutate an installed tag"
            assert colors.read_text() == state_before, (
                "a tag bump must not reset runtime-owned state"
            )
        finally:
            _stop_fake_ags(paths)


class TestLaunchLockWrapper:
    def test_wrapper_registers_and_releases_the_shared_lock(self, tmp_path: Path) -> None:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        _fake_ags(bin_dir)
        _write_wrapper(bin_dir)
        runtime = tmp_path / "runtime"
        runtime.mkdir()
        registry = tmp_path / "registry"
        env = dict(
            os.environ,
            XDG_RUNTIME_DIR=str(runtime),
            FAKE_AGS_REGISTRY=str(registry),
            FAKE_AGS_RUN_SECONDS="30",
            PATH=f"{bin_dir}:{os.environ.get('PATH', '')}",
        )
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        (app_dir / "app.manifest.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "app": "fake-app",
                    "instance": "fake-app",
                    "configDir": "ags-fake-app",
                    "mode": "live",
                    "holdsUnsavedState": False,
                }
            )
        )
        try:
            first = subprocess.run(
                [
                    str(bin_dir / "ags-run-locked"),
                    "--expect-instance",
                    "fake-app",
                    "-d",
                    str(app_dir),
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert first.returncode == 0, first.stderr
            assert (runtime / "ags-launch.lock").exists()
            # A matching expected instance is a delegation no-op.
            second = subprocess.run(
                [
                    str(bin_dir / "ags-run-locked"),
                    "--expect-instance",
                    "fake-app",
                    "-d",
                    str(app_dir),
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert second.returncode == 0, second.stderr
        finally:
            if registry.exists():
                subprocess.run(
                    [str(bin_dir / "ags"), "quit", "-i", "fake-app"], env=env, check=False
                )
                for pidfile in registry.parent.glob(registry.name + ".*.pid"):
                    pidfile.unlink(missing_ok=True)
                registry.unlink(missing_ok=True)

    def test_wrapper_times_out_when_the_lock_is_held(self, tmp_path: Path) -> None:
        import fcntl

        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        _fake_ags(bin_dir)
        _write_wrapper(bin_dir)
        runtime = tmp_path / "runtime"
        runtime.mkdir()
        lock = runtime / "ags-launch.lock"
        env = dict(
            os.environ,
            XDG_RUNTIME_DIR=str(runtime),
            FAKE_AGS_REGISTRY=str(tmp_path / "registry"),
            PATH=f"{bin_dir}:{os.environ.get('PATH', '')}",
        )
        with lock.open("w") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            result = subprocess.run(
                [
                    str(bin_dir / "ags-run-locked"),
                    "--expect-instance",
                    "fake-app",
                    "--lock-timeout",
                    "1",
                    "-d",
                    str(tmp_path),
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
        assert result.returncode == 1
        assert "timed out waiting for the shared AGS launch lock" in result.stderr
