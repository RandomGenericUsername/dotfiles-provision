from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from tests.support import composition_root


def _find_ansible_dir() -> Path:
    """Locate the real ansible scaffold dir by walking up from this test file.

    Mirrors ``test_packages_role.py``: anchored on ``pyproject.toml`` so the
    sibling project's ``ansible/`` tree in a shared workspace is never matched.
    """
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "ansible" / "inventory" / "localhost.yaml"
        if candidate.is_file() and (parent / "pyproject.toml").is_file():
            return parent / "ansible"
    raise FileNotFoundError(
        "src/provisioning/ansible/ not found walking up from the test file; "
        "AC 1-5 real-scaffold coverage requires the authored role"
    )


_ANSIBLE_DIR = _find_ansible_dir()
_ROLES_DIR = _ANSIBLE_DIR / "roles" / "cli_tools"
_REPO_ROOT = composition_root()
_MANIFEST_PATH = _REPO_ROOT / "dotfiles" / "provisioning" / "cli-tools.yaml"

#: Any release-tag literal. Role expressions and task code must derive the pin
#: from the manifest entry, so a match means a hardcoded pin that a bump misses.
_TAG_LITERAL = re.compile(r"\bv\d+\.\d+\.\d+\b")

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


def _load_tasks() -> list[dict[str, object]]:
    data = yaml.safe_load((_ROLES_DIR / "tasks" / "main.yml").read_text())
    assert isinstance(data, list)
    return data


def _module_key(task: dict[str, object]) -> str | None:
    """Return the module FQCN key for a task, or None for bare-key tasks."""
    for key in task:
        if key not in _TASK_KEYWORDS and key != "with_items":
            return key
    return None


def _creates_value(task: dict[str, object]) -> object | None:
    """Return the ``creates`` value whether declared top-level or in args."""
    direct = task.get("creates")
    if direct is not None:
        return direct
    args = task.get("args")
    if isinstance(args, dict):
        return args.get("creates")
    return None


def _manifest_entries() -> list[dict[str, str]]:
    data = yaml.safe_load(_MANIFEST_PATH.read_text())
    assert isinstance(data, dict)
    entries = data["entries"]
    assert isinstance(entries, list)
    return [dict(item) for item in entries]


def _install_tasks() -> list[dict[str, object]]:
    """The tasks that run `uv tool install` for source-path entries.

    Only the FIRST-install task (the one carrying the `creates:` guard)
    counts; the upgrade task (`--force`, 2026-09-07) and the pinned-checkout
    install (which is `--force` by design, so a pin bump is never masked by
    `creates:`) are separate and have their own locks."""
    return [
        task
        for task in _load_tasks()
        if "uv tool install" in str(task.get(_module_key(task) or "", ""))
        if "--force" not in str(task.get(_module_key(task) or "", ""))
    ]


def _force_install_tasks() -> list[dict[str, object]]:
    """The tasks that re-pin a tool env on every run (`uv tool install --force`)."""
    return [
        task
        for task in _load_tasks()
        if "uv tool install --force" in str(task.get(_module_key(task) or "", ""))
    ]


def _role_vars() -> dict[str, object]:
    data = yaml.safe_load((_ROLES_DIR / "vars" / "main.yml").read_text())
    assert isinstance(data, dict)
    return data


def _role_entries() -> list[dict[str, object]]:
    return [dict(item) for item in _role_vars()["cli_tools"]]


def _entry_is_pinned(entry: dict[str, object]) -> bool:
    return "repo" in entry or "tag" in entry


def _assert_one_addressing_shape(entry: dict[str, object]) -> None:
    """A cli_tools entry carries `source` XOR (`repo` + `tag`) — spine AD-10.

    Both shapes are valid during the extraction window; an entry with neither
    installs nothing while still passing name validation, and an entry with
    both hides which address is authoritative (a local path would silently win
    for one consumer while the others resolve the tag)."""
    has_source = "source" in entry
    has_repo = "repo" in entry
    has_tag = "tag" in entry
    assert not (has_source and (has_repo or has_tag)), (
        f"{entry.get('name')!r} carries both source and repo/tag — a CLI-tools "
        "entry addresses exactly one of an in-repo source or a pinned repo+tag"
    )
    assert has_source or (has_repo and has_tag), (
        f"{entry.get('name')!r} carries neither a source nor a repo+tag pair — "
        "the role could not install it"
    )


def _argv_of(task: dict[str, object]) -> list[str] | None:
    """Return the argv list of a task, or None when the module body is not an
    argv-form command (e.g. free-form `command: string` tasks)."""
    module = task.get(_module_key(task) or "", {})
    if not isinstance(module, dict):
        return None
    argv = module.get("argv")
    if not isinstance(argv, list):
        return None
    return [str(item) for item in argv]


def _image_build_tasks() -> list[dict[str, object]]:
    """The tasks that build CLI container images (argv `<cli> install ...`)."""
    return [
        task
        for task in _load_tasks()
        if (_argv_of(task) or [])[1:2] == ["install"]
    ]


def _cli_tools_image_builds() -> list[dict[str, object]]:
    """The role's image-build entries.

    `cli_tools_image_builds` is a SELECTION over the manifest mirror
    (`cli_tools | selectattr('name', 'in', cli_tools_image_build_names)`), not
    a second hand-written list — so the build context and the image tag come
    from the entry's own addressing shape (source XOR repo+tag). This helper
    applies that same selection to the parsed mirror.
    """
    data = yaml.safe_load((_ROLES_DIR / "vars" / "main.yml").read_text())
    names = [str(name) for name in data["cli_tools_image_build_names"]]
    entries = [dict(entry) for entry in data["cli_tools"]]
    return [entry for entry in entries if str(entry.get("name")) in names]


class TestCliToolsRoleTree:
    _REQUIRED_FILES = ("tasks/main.yml", "vars/main.yml")

    def test_role_tree_exists(self) -> None:
        for relative in self._REQUIRED_FILES:
            assert (_ROLES_DIR / relative).is_file(), f"missing {relative}"

    def test_rofi_launcher_is_a_keybound_toggle(self) -> None:
        """`rofi-ui` is the single open/close entrypoint for the SUPER+D bind.

        It closes a live rofi (the pidfile rofi writes + a /proc comm check so
        a stale/recycled PID is never signalled, then SIGTERM) and launches
        otherwise. The KEY must not appear in the script — that is exactly what
        keeps open and close in sync when the bind in keybindings.lua changes.
        """
        template = (_ROLES_DIR / "templates" / "rofi-ui.j2").read_text()
        assert "-pid" in template, "rofi-ui must pin the pidfile rofi writes"
        assert "kill -TERM" in template, "rofi-ui must close a live rofi"
        assert "/proc/" in template and "comm" in template, (
            "rofi-ui must confirm the pid is still rofi before signalling"
        )
        assert "exec rofi -config" in template, "rofi-ui must launch rofi when down"
        assert "SUPER" not in template, (
            "the key must live only in keybindings.lua; rofi-ui must stay key-agnostic"
        )


class TestCliToolsTasks:
    def test_tasks_parse_to_list_of_named_tasks(self) -> None:
        tasks = _load_tasks()
        assert tasks, "tasks/main.yml must not be empty"
        for task in tasks:
            assert isinstance(task, dict)
            assert task["name"], "every task must carry a name"

    def test_install_tasks_cover_all_manifest_entries(self) -> None:
        """Locks AC2: every manifest entry must be installed by a `uv tool
        install` task. TWO install paths remain — a `creates:`-guarded
        source-path install (now empty) and a `--force` install from the
        tag-bearing checkout (all four entries after REQ-002) — so the pair
        still covers both addressing shapes while every entry is pinned."""
        source_tasks = [
            task
            for task in _install_tasks()
            if "uv tool install" in str(task.get(_module_key(task) or "", ""))
        ]
        assert len(source_tasks) == 1, "expected one source-path install task"
        assert source_tasks[0].get("loop") == "{{ cli_tools_source_entries }}"

        pinned_tasks = [
            task
            for task in _force_install_tasks()
            if str(task.get("loop")) == "{{ cli_tools_pinned }}"
        ]
        assert len(pinned_tasks) == 1, "expected one pinned-checkout install task"

        manifest_entries = _manifest_entries()
        assert not any("source" in entry for entry in manifest_entries), (
            "REQ-002 moved the runtime to its pinned repo; no entry carries `source`"
        )
        assert all(_entry_is_pinned(entry) for entry in manifest_entries), (
            "every manifest entry must be `{name, repo, tag}`"
        )

    def test_install_task_creates_guard_is_dry_run_and_idempotent(self) -> None:
        """Locks AC5: `creates: {{ cli_tools_bin_dir }}/{{ item.name }}` is the
        ONLY mechanism on the source-path install task — check-mode-safe by
        construction (filesystem check, not a registered rc). The pinned
        install is `--force` on purpose: a pin bump must re-install even when
        the binary already exists."""
        install_tasks = _install_tasks()
        assert install_tasks, "no uv tool install task found"
        for task in install_tasks:
            creates = _creates_value(task)
            assert creates == "{{ cli_tools_bin_dir }}/{{ item.name }}", (
                f"install task {task.get('name')!r} must carry "
                "creates: '{{ cli_tools_bin_dir }}/{{ item.name }}'"
            )
        for task in _force_install_tasks():
            assert _creates_value(task) is None, (
                f"force install task {task.get('name')!r} must NOT carry creates: "
                "(a pin/version bump must re-install, not be masked by existence)"
            )

    def test_install_task_not_gated_on_presence_check_rc(self) -> None:
        """Locks the Story 2.3 check-mode lesson: under --check a skipped
        `command -v` registers rc=0, so gating the install on a presence-check
        rc would report `skipped` instead of would-change."""
        install_tasks = _install_tasks()
        assert install_tasks, "no uv tool install task found"
        for task in install_tasks:
            when = str(task.get("when", ""))
            assert "uv_check" not in when and "command -v" not in when, (
                f"install task {task.get('name')!r} must not gate on a presence-check rc"
            )

    def test_upgrade_tasks_repin_from_current_source(self) -> None:
        """Upgrade-after-install lock (2026-09-07): a `--force` re-pin task
        must exist for the source-path entries, WITHOUT a `creates:` guard (the
        first-install `creates:` guard alone let already-provisioned machines
        run stale tool envs forever), gated off check-mode, and pinned to the
        same UV_TOOL_BIN_DIR as the install task. Pinned repo entries re-pin
        from their tag-bearing checkout the same way."""
        upgrade_tasks = _force_install_tasks()
        assert len(upgrade_tasks) == 2, (
            "expected the source-path upgrade loop and the pinned-checkout "
            f"install loop, found {len(upgrade_tasks)}"
        )
        loops = {str(task.get("loop")) for task in upgrade_tasks}
        assert loops == {"{{ cli_tools_source_entries }}", "{{ cli_tools_pinned }}"}
        for task in upgrade_tasks:
            environment = task.get("environment")
            assert isinstance(environment, dict)
            assert environment["UV_TOOL_BIN_DIR"] == "{{ cli_tools_bin_dir }}"
            assert task.get("when") == "not ansible_check_mode"
            assert _creates_value(task) is None, (
                "force task must NOT carry creates: (must re-pin every run)"
            )

    def test_uv_presence_check_is_shell_based(self) -> None:
        """F1 lock: `command -v uv` must run via ansible.builtin.shell — the
        command module execs argv directly and `command` is a shell builtin,
        not a binary, so it returns rc=2 on every host and the assert below
        would fail even when uv is installed."""
        checks = [
            task
            for task in _load_tasks()
            if "command -v uv" in str(task.get(_module_key(task) or "", ""))
        ]
        assert checks, "no `command -v uv` presence check task found"
        for task in checks:
            assert _module_key(task) == "ansible.builtin.shell", (
                "uv presence check must use ansible.builtin.shell (command -v is a shell builtin)"
            )
            assert task.get("failed_when") is False
            assert task.get("changed_when") is False

    def test_verify_task_prepends_bin_dir_to_path(self) -> None:
        """Locks AC3 + F1: a verify task resolves each binary with the uv bin
        dir prepended to PATH in the run context. `command -v` is a shell
        builtin (no /usr/bin/command executable), so it MUST run via
        ansible.builtin.shell, never ansible.builtin.command."""
        verify_tasks = [
            task
            for task in _load_tasks()
            if "command -v {{ item.name }}" in str(task.get(_module_key(task) or "", ""))
        ]
        assert verify_tasks, "no `command -v {{ item.name }}` verify task found"
        for task in verify_tasks:
            assert _module_key(task) == "ansible.builtin.shell", (
                "verify task must use ansible.builtin.shell (command -v is a shell builtin)"
            )
            assert task.get("changed_when") is False
            env = task.get("environment")
            assert isinstance(env, dict), "verify task must set environment"
            assert env.get("PATH", "").startswith("{{ cli_tools_bin_dir }}:"), (
                "verify task must prepend cli_tools_bin_dir to PATH (AC 3)"
            )

    def test_capture_tool_is_not_installed_by_this_role(self) -> None:
        """The capture-tool backend ships in the standalone capture app tag.

        cli_tools runs BEFORE ags_apps_units on the bootstrap chain, so it cannot
        install or assert the CLI anymore. The retired copy task must not come
        back: it would install this checkout's old backend over the unit's
        pinned one (two sources of truth).
        """
        tasks_text = (_ROLES_DIR / "tasks" / "main.yml").read_text()
        assert "src/gui-tools/capture-tool" not in tasks_text, (
            "cli_tools must not install the capture-tool backend — ags_apps_units "
            "links the app tag's bin entry"
        )
        assert not any(
            "capture-tool" in str(task.get("name", "")) for task in _load_tasks()
        ), "no cli_tools task may install or verify capture-tool anymore"
        assert not any(
            "command -v capture-tool" in str(task.get(_module_key(task) or "", ""))
            for task in _load_tasks()
        ), "the capture-tool PATH assertion lives with ags_apps_units (after the link)"

    def test_no_become_anywhere_in_role(self) -> None:
        """User-scoped privilege context: `uv tool install` targets the
        intended user, never root (running as root would install into
        /root/.local/bin and AC 3 would be silently false)."""
        for task in _load_tasks():
            assert "become" not in task, (
                f"task {task.get('name')!r} must not use become (user-scoped role)"
            )
            assert "become_user" not in task

    def test_no_absolute_repo_paths_hardcoded(self) -> None:
        """Every source is derived from a seam var, never an absolute repo
        path baked into the task: in-repo entries use
        `{{ cli_tools_composition_root }}/{{ item.source }}`, pinned entries use the
        tag-qualified `{{ cli_tools_checkout_root }}/<name>/<tag>`."""
        for task in _install_tasks():
            command = str(task.get("ansible.builtin.command", ""))
            assert "uv tool install" in command, (
                f"install task {task.get('name')!r} must run `uv tool install`"
            )
            assert "{{ cli_tools_composition_root }}/" in command, (
                f"install task {task.get('name')!r} must use "
                "'{{ cli_tools_composition_root }}/{{ item.source }}'"
            )
            assert "{{ item.source }}" in command
            assert "{{ cli_tools_composition_root }}/" in command.replace("'", ""), (
                "repo source must be interpolated, never an absolute literal"
            )
        pinned_tasks = [
            task
            for task in _force_install_tasks()
            if str(task.get("loop")) == "{{ cli_tools_pinned }}"
        ]
        assert len(pinned_tasks) == 1, "expected one pinned-checkout install task"
        command = str(pinned_tasks[0].get("ansible.builtin.command", ""))
        assert "{{ cli_tools_checkout_root }}/{{ item.name }}/{{ item.tag }}" in command, (
            "the pinned install must address the tag-bearing checkout"
        )
        assert "git+" not in command, (
            "AD-10: install from the checkout, never a git+…@tag URL (PEP 610 "
            "must record a path that names the tag)"
        )
        for task in _load_tasks():
            assert "/home/" not in str(task), (
                f"task {task.get('name')!r} hardcodes a home path"
            )


class TestCliToolsStaleDirectUrl:
    """R-14: force-install rewrites direct_url.json; the post-install assert
    proves a stale file:// checkout cannot survive the run."""

    def test_post_install_assert_scans_direct_url(self) -> None:
        tasks = _load_tasks()
        task = next(
            t
            for t in tasks
            if "direct_url" in str(t.get("name", ""))
        )
        assert _module_key(task) == "ansible.builtin.shell"
        params = task["ansible.builtin.shell"]
        assert isinstance(params, dict)
        cmd = str(params.get("cmd", ""))
        assert "direct_url.json" in cmd
        assert "file://" in cmd
        assert "raise SystemExit(1)" in cmd
        assert task.get("changed_when") is False
        when = str(task.get("when"))
        assert "not ansible_check_mode" in when

    def test_post_install_assert_follows_the_force_installs(self) -> None:
        tasks = _load_tasks()
        names = [str(t.get("name", "")) for t in tasks]
        install = next(
            i for i, name in enumerate(names) if "Upgrade source-path CLI tool envs" in name
        )
        check = next(i for i, name in enumerate(names) if "direct_url" in name)
        assert install < check, "the scan must follow the force re-install it verifies"


class TestCliToolsCodexShadowCleanup:
    """provision-ai-ides-and-clis: the AUR openai-codex-bin owns /usr/bin/codex,
    but OpenAI's standalone installer leaves a self-updating symlink at
    <bin>/codex that precedes /usr/bin on PATH. The role removes it — guarded
    so a user's own codex is never touched — and drops the standalone payload
    while preserving ~/.codex config/auth."""

    @staticmethod
    def _shadow_stat_task() -> dict[str, object]:
        tasks = [
            task
            for task in _load_tasks()
            if task.get("register") == "cli_tools_codex_shadow"
        ]
        assert len(tasks) == 1, "expected exactly one stat of the codex shadow"
        return tasks[0]

    def test_shadow_symlink_is_removed_only_when_standalone(self) -> None:
        stat_task = self._shadow_stat_task()
        module = stat_task.get(_module_key(stat_task) or "", {})
        assert module.get("path") == "{{ cli_tools_bin_dir }}/codex"

        removals = [
            task
            for task in _load_tasks()
            if _module_key(task) == "ansible.builtin.file"
            and task.get(_module_key(task), {}).get("state") == "absent"
            and task.get(_module_key(task), {}).get("path") == "{{ cli_tools_bin_dir }}/codex"
        ]
        assert len(removals) == 1, "expected exactly one codex-shadow removal task"
        when = str(removals[0].get("when"))
        assert "not ansible_check_mode" in when, "shadow removal must be check-mode gated"
        assert "cli_tools_codex_shadow.stat.islnk" in when, (
            "must only remove a symlink (never a user's regular file)"
        )
        assert "/.codex/packages/standalone/" in when, (
            "must only remove the standalone installer's symlink"
        )

    def test_standalone_payload_removed_with_config_preserved(self) -> None:
        checks = [
            task
            for task in _load_tasks()
            if task.get("register") == "cli_tools_codex_standalone"
        ]
        assert len(checks) == 1, "expected a standalone-payload existence check"
        payload_module = checks[0].get(_module_key(checks[0]) or "", {})
        assert payload_module.get("path") == "{{ ansible_facts.env.HOME }}/.codex/packages/standalone"

        removals = [
            task
            for task in _load_tasks()
            if _module_key(task) == "ansible.builtin.file"
            and task.get(_module_key(task), {}).get("state") == "absent"
            and task.get(_module_key(task), {}).get("path") == "{{ ansible_facts.env.HOME }}/.codex/packages"
        ]
        assert len(removals) == 1, "expected the standalone packages payload removal"
        when = str(removals[0].get("when"))
        assert "not ansible_check_mode" in when
        assert "cli_tools_codex_standalone.stat.exists" in when
        # ~/.codex/config.toml and auth must never be named for removal.
        for task in removals:
            assert "config.toml" not in str(task), "user codex config must be preserved"


class TestCliToolsImageBuildTasks:
    def test_image_build_task_loops_over_configured_clis(self) -> None:
        """Container mode (product decision 2026-08-12) requires the cli_tools
        role to build the csg AND weg container images — `uv tool install`
        only installs the host-side launchers. S6 split the pinned loop by TAG
        TRANSPORT (weg takes `--image-tag` on argv; csg's `install` verb reads the
        tag from settings env) and kept the legacy source-path loop, so the
        three loops must together cover exactly the configured names."""
        tasks = _image_build_tasks()
        assert len(tasks) == 4, (
            "expected the argv-tag, env-tag (argv context), env-tag (env "
            "context) and source-build loops (AD-7)"
        )
        loops = " ".join(str(task.get("loop")) for task in tasks)
        assert "cli_tools_image_tag_flag_builds" in loops, (
            "one pinned loop must build the CLIs whose verb takes --image-tag"
        )
        assert "cli_tools_image_tag_env_flag_context_builds" in loops, (
            "one pinned loop must build the env-tag CLIs that take --context"
        )
        assert "cli_tools_image_tag_env_context_builds" in loops, (
            "one pinned loop must build the env-tag CLIs whose context travels "
            "via env (tpr has no --context)"
        )
        assert "rejectattr('tag', 'defined')" in loops, (
            "the legacy source-path loop must still select source entries"
        )
        names = {b["name"] for b in _cli_tools_image_builds()}
        assert {"csg", "weg", "tpr"} <= names, "csg, weg and tpr must all be image-built"

    def test_image_builds_derive_from_the_manifest_mirror(self) -> None:
        """AD-7 'the tag is the pin, not latest', kept as ONE source: the image
        build list is derived from the `cli_tools` mirror (which the parity test
        locks to the manifest), so the tag value is the manifest tag — never a
        hardcoded duplicate. The only pin literal lives in the `cli_tools`
        entry."""
        data = yaml.safe_load((_ROLES_DIR / "vars" / "main.yml").read_text())
        expression = str(data["cli_tools_image_builds"])
        assert "cli_tools" in expression and "selectattr" in expression, (
            "cli_tools_image_builds must select the entries from the manifest "
            "mirror instead of restating paths/tags"
        )
        assert _TAG_LITERAL.search(expression) is None, (
            "the image-build selection must not carry a tag literal — "
            "that comes from the cli_tools entry"
        )
        assert "src/cli-tools" not in expression, (
            "the image-build selection must not carry a source path literal"
        )
        # The transport split is a SELECTION over the same list, never a second
        # hand-written list of names: both halves derive from the entries.
        for var in ("cli_tools_image_tag_flag_builds", "cli_tools_image_tag_env_builds"):
            expression = str(data[var])
            assert "cli_tools_image_builds" in expression, (
                f"{var} must partition cli_tools_image_builds, not restate it"
            )
            assert _TAG_LITERAL.search(expression) is None, (
                f"{var} must not carry a tag literal"
            )
        # The env split for CONTEXT transport is a selection over the env-tag
        # builds, never a second hardcoded name list.
        for var in (
            "cli_tools_image_tag_env_flag_context_builds",
            "cli_tools_image_tag_env_context_builds",
        ):
            expression = str(data[var])
            assert "cli_tools_image_tag_env_builds" in expression, (
                f"{var} must partition cli_tools_image_tag_env_builds"
            )
            assert _TAG_LITERAL.search(expression) is None, (
                f"{var} must not carry a tag literal"
            )
        assert data["cli_tools_image_context_env_keys"] == {
            "tpr": "THEME_PRODUCER_SOURCE_ROOT"
        }, "only tpr takes its build context through oci_runtime's env override"
        flag_names = [str(n) for n in data["cli_tools_image_tag_flag_names"]]
        assert flag_names == ["weg"], (
            "weg's install verb takes --image-tag; csg and tpr do not, so they "
            "must be built through the env transport"
        )
        expected_tags = {"csg": "v0.2.1", "weg": "v0.2.0", "tpr": "v0.1.0"}
        for entry in _cli_tools_image_builds():
            assert entry.get("tag") == expected_tags[str(entry.get("name"))], (
                f"{entry.get('name')} image tag must be the pinned repo tag"
            )
        env_keys = data["cli_tools_image_tag_env_keys"]
        assert env_keys == {
            "csg": "COLORSCHEME__CONTAINER__IMAGE_TAG",
            "tpr": "THEME__CONTAINER__IMAGE_TAG",
        }, (
            "each env-tag build must carry its own settings prefix (REQ-010); "
            "a shared key would send tpr's tag to csg's resolver or vice versa"
        )
        env_names = {
            str(e["name"])
            for e in _cli_tools_image_builds()
            if str(e.get("name")) not in flag_names
        }
        assert env_names == set(env_keys), (
            "every env-tag build needs a key in cli_tools_image_tag_env_keys"
        )

    def test_image_build_task_passes_container_engine(self) -> None:
        tasks = _image_build_tasks()
        assert len(tasks) == 4, "expected all four image-build loops"
        declared = "{{ container_runtime_engine }}"
        for task in tasks:
            argv = _argv_of(task)
            assert "--container-engine" in argv
            assert argv[argv.index("--container-engine") + 1] == declared, (
                "image-build task must pass --container-engine from the DECLARED "
                "engine {{ container_runtime_engine }} — the single source of truth "
                "shared with the rendered settings"
            )

    def test_image_build_task_passes_package_context(self) -> None:
        """AD-5/AD-7: the build context is the CLI's own repo, not the dotfiles
        repo root — for a pinned CLI that is the tag-qualified CHECKOUT."""
        tasks = _image_build_tasks()
        assert len(tasks) == 4, "expected all four image-build loops"
        flag = [
            task
            for task in tasks
            if str(task.get("loop")) == "{{ cli_tools_image_tag_flag_builds }}"
        ]
        env_flag_context = [
            task
            for task in tasks
            if str(task.get("loop")) == "{{ cli_tools_image_tag_env_flag_context_builds }}"
        ]
        env_context = [
            task
            for task in tasks
            if str(task.get("loop")) == "{{ cli_tools_image_tag_env_context_builds }}"
        ]
        source = [
            task
            for task in tasks
            if "rejectattr('tag', 'defined')" in str(task.get("loop"))
        ]
        assert (
            len(flag) == 1
            and len(env_flag_context) == 1
            and len(env_context) == 1
            and len(source) == 1
        )

        checkout_context = "{{ cli_tools_checkout_root }}/{{ item.name }}/{{ item.tag }}"
        for pinned in (flag[0], env_flag_context[0]):
            pinned_argv = _argv_of(pinned)
            assert "--context" in pinned_argv, "the build verb now takes --context"
            assert pinned_argv[pinned_argv.index("--context") + 1] == checkout_context, (
                "a pinned CLI builds from its tag-qualified checkout (AD-5/AD-10)"
            )
            assert "--source-root" not in pinned_argv, (
                "--source-root is now a deprecated alias; provisioning uses --context"
            )

        flag_argv = _argv_of(flag[0])
        assert flag_argv[flag_argv.index("--image-tag") + 1] == "{{ item.tag }}", (
            "the image tag must be the PIN from the manifest entry (AD-7)"
        )

        for env_task in (env_flag_context[0], env_context[0]):
            env_argv = _argv_of(env_task)
            assert "--image-tag" not in env_argv, (
                "csg/tpr install verbs have no --image-tag; it must not be passed"
            )
            env_body = env_task.get("environment")
            # Ansible templates env VALUES but not literal mapping KEYS, so the
            # task builds the whole dict as an expression (verified against
            # ansible-playbook: a quoted key reached the module as a literal
            # `{{ ... }}` env name). Assert the expression, not a static dict.
            assert isinstance(env_body, str), (
                "the env-tag transport must build the environment as an "
                "expression so the per-tool key resolves before the module runs"
            )
            assert "cli_tools_image_tag_env_keys[item.name]" in env_body
            assert "item.tag" in env_body
            assert "cli_tools_bin_dir" in env_body and "PATH" in env_body, (
                "the build must keep the pinned bin dir on PATH"
            )
            assert "COLORSCHEME__CONTAINER__IMAGE_TAG" not in str(env_task), (
                "the csg key must not be hardcoded in the task anymore — it "
                "lives in cli_tools_image_tag_env_keys so tpr can carry its own "
                "prefix"
            )

        # tpr has no --context: its checkout travels as THEME_PRODUCER_SOURCE_ROOT
        # (oci_runtime's explicit override), never via implicit PEP 610.
        assert "--context" not in _argv_of(env_context[0]), (
            "tpr's install verb has no --context option"
        )
        context_env = str(env_context[0].get("environment"))
        assert "cli_tools_image_context_env_keys[item.name]" in context_env
        assert "cli_tools_checkout_root" in context_env and "item.tag" in context_env

        source_argv = _argv_of(source[0])
        assert source_argv[source_argv.index("--context") + 1] == (
            "{{ cli_tools_composition_root }}/{{ item.source }}"
        ), "a source-path CLI builds from its in-repo package dir"
        assert "--image-tag" not in source_argv, (
            "a source-only CLI has no pin to pass as its tag"
        )
        assert source[0].get("environment", {}).get(
            "COLORSCHEME__CONTAINER__IMAGE_TAG"
        ) is None, "the legacy source build must not carry the csg env tag"

    def test_image_build_tasks_have_no_hardcoded_image_tag(self) -> None:
        """AD-7/AD-11: the tag comes from the manifest entry at task time, so a
        pin bump needs no task edit and no task can silently build `latest`."""
        for task in _image_build_tasks():
            text = str(task)
            assert "latest" not in text, (
                f"image-build task {task.get('name')!r} must never name `latest`"
            )
            assert _TAG_LITERAL.search(text) is None, (
                f"image-build task {task.get('name')!r} must not hardcode the pin"
            )

    def test_image_build_task_is_check_mode_gated(self) -> None:
        """Command modules execute under --check, so the image build must be
        gated `when: not ansible_check_mode` (dry-run must stay dry)."""
        tasks = _image_build_tasks()
        assert tasks, "expected an image-build task"
        for task in tasks:
            assert "not ansible_check_mode" in str(task.get("when", "")), (
                f"image-build task {task.get('name')!r} must be check-mode gated"
            )

    def test_image_build_task_has_no_creates_guard(self) -> None:
        """Image EXISTENCE does not imply FRESHNESS: a `creates:` guard would
        skip rebuilding a stale image (the exact defect this chain fixes)."""
        tasks = _image_build_tasks()
        assert tasks, "expected an image-build task"
        for task in tasks:
            assert _creates_value(task) is None, (
                f"image-build task {task.get('name')!r} must NOT carry creates: "
                "(existence != freshness)"
            )

    def test_no_become_on_image_build_tasks(self) -> None:
        tasks = _image_build_tasks()
        for task in tasks:
            assert "become" not in task, (
                f"image-build task {task.get('name')!r} must not use become "
                "(rootless podman builds into the user storage)"
            )


class TestCliToolsEngineAssertionBattery:
    """Option 2b: one DECLARED engine (container_runtime_engine), validated by a
    four-layer fail-loud battery — domain → presence → usability → capability
    smoke. There is NO detection probe and NO resolved-engine set_fact."""

    def test_no_detection_probe_and_no_resolved_engine_set_fact(self) -> None:
        for task in _load_tasks():
            body = str(task.get(_module_key(task) or "", ""))
            assert "command -v podman" not in body, (
                "engine detection must be removed — the engine is DECLARED, "
                "never probed for a podman/docker preference"
            )
            assert "container_runtime_engine" not in body or _module_key(task) != "ansible.builtin.set_fact", (
                "no set_fact may resolve an engine — container_runtime_engine is "
                "declared in group_vars/all.yml"
            )

    def test_layer1_domain_assert_is_ungated_and_names_both_remedies(self) -> None:
        asserts = [
            task
            for task in _load_tasks()
            if _module_key(task) == "ansible.builtin.assert"
            and 'container_runtime_engine in ["podman", "docker"]'
            in str(task.get("ansible.builtin.assert", ""))
        ]
        assert asserts, "expected the Layer-1 domain assert"
        for task in asserts:
            assert task.get("when") is None, (
                "the domain assert must be UNGATED (runs under --check too)"
            )
            msg = str(task.get("ansible.builtin.assert", {}).get("fail_msg", ""))
            assert "container_runtime_engine" in msg
            assert "-e container_runtime_engine=" in msg
            assert "DOTFILES_CONTAINER_ENGINE=" in msg

    @staticmethod
    def _task_with_register(register: str) -> dict[str, object]:
        matches = [task for task in _load_tasks() if task.get("register") == register]
        assert len(matches) == 1, f"expected exactly one task registering {register!r}"
        return matches[0]

    @staticmethod
    def _asserts_mentioning(fragment: str) -> list[dict[str, object]]:
        return [
            task
            for task in _load_tasks()
            if _module_key(task) == "ansible.builtin.assert"
            and fragment in str(task.get("ansible.builtin.assert", ""))
        ]

    def test_layer2_presence_probe_and_gated_assert(self) -> None:
        probe = self._task_with_register("cli_tools_engine_presence")
        assert _module_key(probe) == "ansible.builtin.shell", (
            "command -v is a shell builtin — the presence probe must use shell"
        )
        assert "command -v {{ container_runtime_engine }}" in str(
            probe.get("ansible.builtin.shell", "")
        )
        assert probe.get("changed_when") is False
        assert probe.get("failed_when") is False
        assert probe.get("when") == "not ansible_check_mode", (
            "the presence probe must be gated (shell never runs under --check)"
        )
        env = probe.get("environment")
        assert isinstance(env, dict)
        assert env.get("PATH", "").startswith("{{ cli_tools_bin_dir }}:")

        asserts = self._asserts_mentioning("cli_tools_engine_presence.rc == 0")
        assert asserts, "expected the presence assert"
        for task in asserts:
            assert task.get("when") == "not ansible_check_mode"

    def test_layer3_usability_probe_is_bounded_and_assert_gated(self) -> None:
        probe = self._task_with_register("cli_tools_engine_usability")
        assert _module_key(probe) == "ansible.builtin.shell"
        assert "timeout 30 {{ container_runtime_engine }} info" in str(
            probe.get("ansible.builtin.shell", "")
        ), "usability probe must be bounded (`timeout 30 ... info`)"
        assert probe.get("changed_when") is False
        assert probe.get("failed_when") is False
        assert probe.get("when") == "not ansible_check_mode"

        asserts = self._asserts_mentioning("cli_tools_engine_usability.rc == 0")
        assert asserts, "expected the usability assert"
        for task in asserts:
            assert task.get("when") == "not ansible_check_mode"

    def test_layer4_capability_smoke_battery(self) -> None:
        # Probe file (tempfile) — gated.
        tempfile_tasks = [task for task in _load_tasks() if task.get("register") == "probe"]
        assert len(tempfile_tasks) == 1, "expected exactly one smoke probe tempfile task"
        tempfile_task = tempfile_tasks[0]
        assert _module_key(tempfile_task) == "ansible.builtin.tempfile"
        tempfile_body = tempfile_task.get("ansible.builtin.tempfile", {})
        assert tempfile_body.get("state") == "file"
        assert tempfile_body.get("prefix") == "weg-container-smoke-"
        assert tempfile_task.get("when") == "not ansible_check_mode"

        # Copy content into the probe file — gated.
        copy_tasks = [
            task
            for task in _load_tasks()
            if _module_key(task) == "ansible.builtin.copy"
            and task.get("ansible.builtin.copy", {}).get("dest") == "{{ probe.path }}"
        ]
        assert len(copy_tasks) == 1, "expected the smoke probe content write"
        copy_task = copy_tasks[0]
        copy_body = copy_task.get("ansible.builtin.copy", {})
        assert "weg-container-smoke" in str(copy_body.get("content", ""))
        assert copy_body.get("mode") == "0644"
        assert copy_task.get("when") == "not ansible_check_mode"

        # The run itself: argv-form command, gated, probes changed/failed false.
        run = self._task_with_register("cli_tools_engine_smoke")
        assert _module_key(run) == "ansible.builtin.command", (
            "the smoke run must use argv-form command (NOT shell) so quoting is safe"
        )
        argv = _argv_of(run)
        assert argv is not None
        assert "run" in argv and "--rm" in argv
        assert argv[argv.index("-e") + 1] == "WEG_SMOKE=ok"
        assert "{{ cli_tools_engine_smoke_image }}" in argv
        assert any(":/smoke/probe.txt:ro" in arg for arg in argv), (
            "the smoke must bind-mount the probe file read-only"
        )
        assert argv[0] == "timeout", "the smoke run must be bounded"
        assert run.get("changed_when") is False
        assert run.get("failed_when") is False
        assert run.get("when") == "not ansible_check_mode"

        asserts = self._asserts_mentioning("'SMOKE_OK' in (cli_tools_engine_smoke.stdout")
        assert asserts, "expected the smoke success assert"
        for task in asserts:
            assert task.get("when") == "not ansible_check_mode"
            msg = str(task.get("ansible.builtin.assert", {}).get("fail_msg", ""))
            assert "cli_tools_engine_smoke.rc" in msg
            assert "cli_tools_engine_smoke.stderr" in msg

        # Cleanup — gated file state absent.
        cleanups = [
            task
            for task in _load_tasks()
            if _module_key(task) == "ansible.builtin.file"
            and task.get("ansible.builtin.file", {}).get("path") == "{{ probe.path }}"
            and task.get("ansible.builtin.file", {}).get("state") == "absent"
        ]
        assert len(cleanups) == 1, "expected the smoke probe cleanup"
        assert cleanups[0].get("when") == "not ansible_check_mode"

    def test_battery_tasks_are_all_named_and_never_use_become(self) -> None:
        battery_registers = {
            "cli_tools_engine_presence",
            "cli_tools_engine_usability",
            "cli_tools_engine_smoke",
        }
        for task in _load_tasks():
            assert task.get("name"), "every task must carry a name"
            if task.get("register") in battery_registers:
                assert "become" not in task
                assert "become_user" not in task


class TestCliToolsPinnedCheckout:
    """cli-tools-repos S4 / spine AD-10: itr is consumed from its pinned repo.

    The role shallow-clones `<repo>@<tag>` into `<install>/cli-tools/<name>/<tag>/`,
    removes `.git`, records the tag in `<install>/cli-tools/<name>/pinned`, and
    installs the tool FROM that checkout (never a `git+…@tag` URL, which would
    make PEP 610 record a repository URL instead of the tag-bearing path).
    The clone/remove/install mutations are check-gated exactly like the
    ags_apps_units app-tag clone.
    """

    @staticmethod
    def _pinned_install_task() -> dict[str, object]:
        tasks = [
            task
            for task in _force_install_tasks()
            if str(task.get("loop")) == "{{ cli_tools_pinned }}"
        ]
        assert len(tasks) == 1, "expected exactly one pinned-checkout install task"
        return tasks[0]

    @staticmethod
    def _clone_task() -> dict[str, object]:
        tasks = [
            task
            for task in _load_tasks()
            if _module_key(task) == "ansible.builtin.git"
        ]
        assert len(tasks) == 1, "expected exactly one pinned clone task"
        return tasks[0]

    def test_pinned_entries_are_the_manifest_repo_entries(self) -> None:
        data = _role_vars()
        assert data["cli_tools_checkout_root"] == "{{ install_dir | trim }}/cli-tools", (
            "AD-10 path shape is <install>/cli-tools/<name>/<tag>"
        )
        pinned = [e for e in data["cli_tools"] if _entry_is_pinned(e)]
        assert [e["name"] for e in pinned] == [
            "csg",
            "weg",
            "itr",
            "tpr",
            "dotfiles-runtime",
        ], "every entry is pinned; REQ-010 added theme-producer"
        assert pinned[0]["repo"] == (
            "https://github.com/RandomGenericUsername/color-scheme-generator"
        )
        assert pinned[0]["tag"] == "v0.2.1"
        assert pinned[1]["repo"] == (
            "https://github.com/RandomGenericUsername/wallpaper-effects-generator"
        )
        assert pinned[1]["tag"] == "v0.2.0"
        assert pinned[2]["repo"] == (
            "https://github.com/RandomGenericUsername/icon-templates-renderer"
        )
        assert pinned[2]["tag"] == "v0.2.0"
        assert pinned[3]["repo"] == (
            "https://github.com/RandomGenericUsername/theme-producer"
        )
        assert pinned[3]["tag"] == "v0.1.0"
        assert pinned[4]["repo"] == (
            "https://github.com/RandomGenericUsername/dotfiles-runtime"
        )
        assert pinned[4]["tag"] == "v0.3.0"

    def test_pinned_clone_is_shallow_single_branch_and_tag_qualified(self) -> None:
        task = self._clone_task()
        module = task.get(_module_key(task), {})
        assert isinstance(module, dict)
        assert module.get("repo") == "{{ item.item.repo }}"
        assert module.get("version") == "{{ item.item.tag }}", (
            "the clone must check out the TAG, not a branch head"
        )
        assert module.get("depth") == 1, "the clone must be shallow"
        assert module.get("single_branch") is True
        assert module.get("dest") == (
            "{{ cli_tools_checkout_root }}/{{ item.item.name }}/{{ item.item.tag }}"
        ), "AD-10 path shape is <install>/cli-tools/<name>/<tag>/"

    def test_pinned_clone_is_presence_guarded_and_check_gated(self) -> None:
        task = self._clone_task()
        when = task.get("when")
        assert isinstance(when, list)
        joined = " ".join(str(clause) for clause in when)
        assert "not ansible_check_mode" in joined, "a clone must never run dry"
        assert "item.stat.exists" in joined, (
            "the clone must be presence-guarded by the pyproject.toml marker stat"
        )
        markers = [
            task
            for task in _load_tasks()
            if task.get("register") == "cli_tools_checkouts"
        ]
        assert len(markers) == 1, "expected one checkout marker stat loop"
        marker = markers[0].get(_module_key(markers[0]) or "", {})
        assert marker.get("path") == (
            "{{ cli_tools_checkout_root }}/{{ item.name }}/{{ item.tag }}/pyproject.toml"
        ), "the marker must live inside the tag-qualified checkout"
        assert markers[0].get("loop") == "{{ cli_tools_pinned }}"

    def test_pinned_git_dir_is_removed_idempotently_and_check_gated(self) -> None:
        removals = [
            task
            for task in _load_tasks()
            if _module_key(task) == "ansible.builtin.file"
            and task.get("ansible.builtin.file", {}).get("state") == "absent"
            and str(task.get("ansible.builtin.file", {}).get("path", "")).endswith("/.git")
        ]
        assert len(removals) == 1, "expected exactly one .git removal task"
        task = removals[0]
        assert task.get("ansible.builtin.file", {}).get("path") == (
            "{{ cli_tools_checkout_root }}/{{ item.name }}/{{ item.tag }}/.git"
        )
        assert task.get("when") == "not ansible_check_mode", (
            "removal is idempotent (absent -> no change) but must not run dry"
        )

    def test_pinned_tag_is_recorded_next_to_the_checkout(self) -> None:
        records = [
            task
            for task in _load_tasks()
            if _module_key(task) == "ansible.builtin.copy"
            and str(task.get("ansible.builtin.copy", {}).get("dest", "")).endswith(
                "/pinned"
            )
        ]
        assert len(records) == 1, "expected exactly one pin-record task"
        module = records[0].get("ansible.builtin.copy", {})
        assert module.get("dest") == "{{ cli_tools_checkout_root }}/{{ item.name }}/pinned"
        assert module.get("content") == "{{ item.tag }}\n", (
            "the pin record is a one-line tag (ags_apps_units 'pinned' precedent)"
        )
        assert records[0].get("loop") == "{{ cli_tools_pinned }}"

    def test_pinned_install_is_from_the_checkout_and_force_reinstalls(self) -> None:
        task = self._pinned_install_task()
        command = str(task.get("ansible.builtin.command", ""))
        assert "--force" in command, (
            "a pin bump must re-install even when the binary already exists"
        )
        assert "--no-cache" in command
        assert "{{ cli_tools_checkout_root }}/{{ item.name }}/{{ item.tag }}" in command
        assert "git+" not in command
        environment = task.get("environment")
        assert isinstance(environment, dict)
        assert environment["UV_TOOL_BIN_DIR"] == "{{ cli_tools_bin_dir }}"

    def test_install_dir_seam_is_asserted(self) -> None:
        asserts = [
            task
            for task in _load_tasks()
            if _module_key(task) == "ansible.builtin.assert"
            and "install_dir" in str(task.get("ansible.builtin.assert", ""))
        ]
        assert asserts, "the pinned path needs the install_dir seam asserted"
        assert "install_dir is defined" in str(asserts[0].get("ansible.builtin.assert"))

    def test_verify_path_check_still_covers_all_entries(self) -> None:
        """No regression for csg/weg: the `command -v` post-check loops the
        WHOLE cli_tools list, not just the pinned subset."""
        checks = [
            task
            for task in _load_tasks()
            if "command -v {{ item.name }}" in str(task.get(_module_key(task) or "", ""))
        ]
        assert len(checks) == 1
        assert checks[0].get("loop") == "{{ cli_tools }}"


class TestCliToolsVars:
    def test_vars_parse_with_required_keys(self) -> None:
        data = yaml.safe_load((_ROLES_DIR / "vars" / "main.yml").read_text())
        assert isinstance(data, dict), "vars/main.yml must parse to a dict"
        assert {
            "cli_tools_manifests_dir",
            "cli_tools_composition_root",
            "cli_tools_bin_dir",
            "cli_tools",
        }.issubset(set(data))

    def test_engine_is_declared_not_detected(self) -> None:
        """Option 2b: the engine is DECLARED once
        (`container_runtime_engine` in group_vars/all.yml, shipped default
        podman) and consumed by BOTH the build and the rendered settings — the
        role carries no detection probe and no resolved-engine set_fact, and the
        old override escape hatch is gone."""
        data = yaml.safe_load((_ROLES_DIR / "vars" / "main.yml").read_text())
        assert "cli_tools_container_engine" not in data, (
            "the role must not pin its own engine — container_runtime_engine in "
            "group_vars/all.yml is the single source of truth"
        )
        assert "cli_tools_container_engine_override" not in data, (
            "the old override escape hatch must be deleted (superseded by the "
            "declared container_runtime_engine)"
        )
        assert data.get("cli_tools_engine_smoke_image"), (
            "the Layer-4 smoke must use a pinned image var"
        )

        # No detection probe and no resolved-engine set_fact anywhere in tasks.
        for task in _load_tasks():
            assert "command -v podman" not in str(task.get(_module_key(task) or "", "")), (
                "engine detection must be gone — the engine is DECLARED"
            )
            if _module_key(task) == "ansible.builtin.set_fact":
                assert "container_runtime_engine" not in str(task), (
                    "no set_fact may resolve an engine — it is declared in group_vars"
                )

        # The build consumes the DECLARED engine.
        argv = _argv_of(_image_build_tasks()[0])
        assert argv is not None
        assert argv[argv.index("--container-engine") + 1] == "{{ container_runtime_engine }}"

    def test_image_builds_list_contains_only_container_mode_clis(self) -> None:
        """csg, weg and tpr are container-mode CLIs and must be image-built;
        itr/runtime have no container mode and must not be. Every selected
        entry carries the PINNED shape (repo+tag) — no CLI is source-only."""
        builds = _cli_tools_image_builds()
        names = {str(b["name"]) for b in builds}
        assert names == {"csg", "weg", "tpr"}, (
            "image builds must be exactly the container-mode CLIs"
        )
        by_name = {str(b["name"]): b for b in builds}
        expected_tags = {"csg": "v0.2.1", "weg": "v0.2.0", "tpr": "v0.1.0"}
        for name in ("csg", "weg", "tpr"):
            assert by_name[name].get("repo") and by_name[name].get("tag") == expected_tags[name], (
                f"{name} is pinned — its build context is the tag-qualified "
                f"checkout and its image tag is the pin"
            )
            assert not by_name[name].get("source"), (
                f"{name} must not keep a source path (S6 moved csg out)"
            )

    def test_no_cli_remains_a_source_entry(self) -> None:
        """REQ-002 end state: every entry — csg, weg, itr and the runtime — is
        pinned. The source-path branch remains as an extension point but selects
        nothing; a source entry reappearing silently reopens the mixed shape."""
        data = yaml.safe_load((_ROLES_DIR / "vars" / "main.yml").read_text())
        source_names = [
            str(entry["name"])
            for entry in data["cli_tools"]
            if "source" in entry
        ]
        assert source_names == [], (
            "no CLI may be installed from an in-repo source after REQ-002"
        )

    def test_cli_tools_parity_with_manifest(self) -> None:
        """Parity lock: the role var exactly mirrors the manifest, and every
        entry on BOTH sides carries exactly one addressing shape — `source`
        XOR `repo` + `tag` (spine AD-10). The role and the manifest are
        hand-maintained mirrors, so both the values and the shape are asserted
        together: a pinned entry that lost its tag would install nothing, and
        an entry carrying both would let a local path shadow the pin."""
        role_entries = _role_entries()
        manifest_entries = _manifest_entries()
        assert len(role_entries) == len(manifest_entries)
        assert {tuple(e.items()) for e in role_entries} == {
            tuple(e.items()) for e in manifest_entries
        }
        for entry in role_entries + manifest_entries:
            _assert_one_addressing_shape(entry)

    def test_parity_rejects_a_pinned_entry_without_tag(self) -> None:
        """A repo without a tag has no pin to install; the parity shape lock
        must reject it instead of falling through to a branch head."""
        with pytest.raises(AssertionError):
            _assert_one_addressing_shape(
                {"name": "itr", "repo": "https://example.invalid/itr"}
            )

    def test_parity_rejects_an_entry_with_neither_shape(self) -> None:
        with pytest.raises(AssertionError):
            _assert_one_addressing_shape({"name": "itr"})

    def test_parity_rejects_an_entry_with_both_shapes(self) -> None:
        with pytest.raises(AssertionError):
            _assert_one_addressing_shape(
                {
                    "name": "itr",
                    "source": "src/cli-tools/icon-templates-renderer",
                    "repo": "https://example.invalid/itr",
                    "tag": "v0.1.0",
                }
            )

    def test_parity_accepts_both_valid_shapes(self) -> None:
        _assert_one_addressing_shape({"name": "csg", "source": "src/cli-tools/x"})
        _assert_one_addressing_shape(
            {"name": "itr", "repo": "https://example.invalid/itr", "tag": "v0.1.0"}
        )

    def test_cli_tools_bin_dir_defaults_under_home(self) -> None:
        """uv's bin-dir resolution, in order: UV_TOOL_BIN_DIR -> XDG_BIN_HOME ->
        $HOME/.local/bin. The DECLARED value must fall back to $HOME/.local/bin
        when neither XDG/uv var is set, and must honor the XDG overrides so the
        PATH prepend + `creates` match where uv actually installs (fixes the
        custom-XDG-layout failure where uv wrote to $XDG_DATA_HOME/uv/tools but
        the role looked only at $HOME/.local/bin)."""
        data = yaml.safe_load((_ROLES_DIR / "vars" / "main.yml").read_text())
        value = str(data["cli_tools_bin_dir"])
        assert "UV_TOOL_BIN_DIR" in value
        assert "XDG_BIN_HOME" in value
        assert "ansible_facts.env.HOME + '/.local/bin'" in value

    def test_bin_dir_uses_non_deprecated_env_fact(self) -> None:
        """F4 lock: use ansible_facts.env (not the deprecated top-level
        ansible_env fact injected via INJECT_FACTS_AS_VARS), which hard-breaks
        on ansible-core >= 2.24."""
        data = yaml.safe_load((_ROLES_DIR / "vars" / "main.yml").read_text())
        assert "ansible_facts.env.HOME" in str(data["cli_tools_bin_dir"])
        assert "{{ ansible_env." not in str(data["cli_tools_bin_dir"])


class TestCliToolsPlaybook:
    _PATH = _ANSIBLE_DIR / "playbooks" / "cli-tools.yaml"

    def test_parses_with_simple_localhost_structure(self) -> None:
        plays = yaml.safe_load(self._PATH.read_text())
        assert isinstance(plays, list) and len(plays) == 1
        play = plays[0]
        assert play["hosts"] == "localhost"
        assert play["gather_facts"] is True
        assert play["roles"] == ["cli_tools"]
        assert "become" not in play, "cli-tools playbook must not use become"

    def test_syntax_check_exits_zero(self) -> None:
        ansible_playbook = shutil.which("ansible-playbook")
        if ansible_playbook is None:
            pytest.skip("ansible-playbook not installed; skipping syntax-check")
        env = dict(os.environ)
        env["ANSIBLE_CONFIG"] = str(_ANSIBLE_DIR / "ansible.cfg")
        result = subprocess.run(
            [
                ansible_playbook,
                "--syntax-check",
                str(self._PATH),
                "-e",
                "os_family=arch",
                "-e",
                "install_dir=/tmp/x",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, result.stdout + result.stderr
