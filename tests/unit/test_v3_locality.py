"""Generations v3 deployment/locality contracts for the provisioning engine.

These tests pin the wave-4 boundary from `dotfiles-v3/docs/107-generations-v3.md`
§2.7 and contracts `generations.md` v0.12.0 §6:

- provisioning owns stable links for non-runtime palette consumers and points
  them at `state/current/palette/...`;
- no runtime artifact lives inside an immutable `<install>/apps/<tag>`;
- verify reads the committed generation manifest and appearance targets, but
  tolerates a fresh state root with no generation yet.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


def _find_ansible_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "ansible" / "inventory" / "localhost.yaml"
        if candidate.is_file() and (parent / "pyproject.toml").is_file():
            return parent / "ansible"
    raise FileNotFoundError("ansible/ not found walking up from the test file")


_ANSIBLE_DIR = _find_ansible_dir()
_ROLES_DIR = _ANSIBLE_DIR / "roles"
_STATE_LINKS = _ROLES_DIR / "state_links"
_VERIFY = _ROLES_DIR / "verify"


def _vars(role: str) -> dict[str, object]:
    data = yaml.safe_load((_ROLES_DIR / role / "vars" / "main.yml").read_text())
    assert isinstance(data, dict)
    return data


def _tasks(role: str) -> list[dict[str, object]]:
    data = yaml.safe_load((_ROLES_DIR / role / "tasks" / "main.yml").read_text())
    assert isinstance(data, list)
    return [dict(task) for task in data]


def _module_key(task: dict[str, object]) -> str | None:
    keywords = {
        "name",
        "when",
        "register",
        "changed_when",
        "failed_when",
        "loop",
        "loop_control",
        "vars",
        "environment",
        "tags",
        "become",
        "become_user",
        "check_mode",
        "block",
        "rescue",
        "always",
        "include_tasks",
        "import_tasks",
    }
    for key in task:
        if key not in keywords:
            return key
    return None


def _module(task: dict[str, object]) -> dict[str, object]:
    module = task.get(_module_key(task) or "", {})
    assert isinstance(module, dict)
    return module


def _task(name: str, role: str = "verify") -> dict[str, object]:
    matches = [task for task in _tasks(role) if task.get("name") == name]
    assert len(matches) == 1, f"expected one {name!r} task in {role}; got {len(matches)}"
    return matches[0]


class TestStableConsumerLinks:
    def test_state_links_owns_only_non_runtime_consumers(self) -> None:
        data = _vars("state_links")
        consumers = data["state_links_consumers"]
        assert isinstance(consumers, list)
        assert [
            (item["base"], item["spine"], item["target"]) for item in consumers
        ] == [
            ("palette", "gtk-3.0/colors.css", "colors.gtk.css"),
            ("palette", "gtk-4.0/colors.css", "colors.adw.css"),
            ("palette", "rofi/colors.rasi", "colors.rasi"),
            ("palette", "btop/themes/colors.btop.theme", "colors.btop.theme"),
            ("appearance", "wlogout/appearance.css", "wlogout.css"),
            ("appearance", "gtk-3.0/appearance.css", "gtk3.css"),
            ("appearance", "gtk-4.0/appearance.css", "gtk4.css"),
            ("appearance", "rofi/appearance.rasi", "rofi.rasi"),
            ("appearance", "kitty/appearance.conf", "kitty.conf"),
        ]
        joined = str(data)
        assert "config/ags" not in joined
        assert data["state_links_state_current_palette_dir"] == (
            "{{ state_links_state_current_dir }}/palette"
        )
        assert data["state_links_state_current_appearance_dir"] == (
            "{{ state_links_state_current_dir }}/appearance"
        )

    def test_state_links_target_the_current_pointer_never_a_generation(self) -> None:
        link_tasks = [
            task
            for task in _tasks("state_links")
            if _module_key(task) == "ansible.builtin.file"
            and _module(task).get("state") == "link"
        ]
        assert len(link_tasks) == 1
        module = _module(link_tasks[0])
        assert module["src"] == (
            "{{ state_links_state_current_dir }}/{{ item.base }}/{{ item.target }}"
        )
        assert module["dest"] == "{{ state_links_spine_config_dir }}/{{ item.spine }}"
        assert "install_dir | trim }}/config/{{ item.spine }}" not in str(module["dest"])
        assert "generations" not in str(module["src"])
        assert "/apps/" not in str(module["src"])

    def test_wlogout_appearance_link_names_the_current_appearance_sheet(self) -> None:
        data = _vars("state_links")
        consumer = next(
            item
            for item in data["state_links_consumers"]
            if item["spine"] == "wlogout/appearance.css"
        )
        assert consumer == {
            "base": "appearance",
            "spine": "wlogout/appearance.css",
            "target": "wlogout.css",
        }

    def test_format_aware_appearance_links_name_their_current_targets(self) -> None:
        """F-4.1: GTK3/GTK4/rofi use consumer aliases but real config dirs."""
        data = _vars("state_links")
        by_spine = {
            item["spine"]: item for item in data["state_links_consumers"]
        }
        assert by_spine["gtk-3.0/appearance.css"] == {
            "base": "appearance",
            "spine": "gtk-3.0/appearance.css",
            "target": "gtk3.css",
        }
        assert by_spine["gtk-4.0/appearance.css"] == {
            "base": "appearance",
            "spine": "gtk-4.0/appearance.css",
            "target": "gtk4.css",
        }
        assert by_spine["rofi/appearance.rasi"] == {
            "base": "appearance",
            "spine": "rofi/appearance.rasi",
            "target": "rofi.rasi",
        }
        assert by_spine["kitty/appearance.conf"] == {
            "base": "appearance",
            "spine": "kitty/appearance.conf",
            "target": "kitty.conf",
        }
        # The rofi/kitty artifacts are never linked through a `.css` target.
        assert not by_spine["rofi/appearance.rasi"]["target"].endswith(".css")
        assert not by_spine["kitty/appearance.conf"]["target"].endswith(".css")

    def test_post_seed_playbook_runs_config_links_then_state_links(self) -> None:
        playbook = yaml.safe_load(
            (_ANSIBLE_DIR / "playbooks" / "config-links-post-seed.yaml").read_text()
        )
        assert playbook[0]["roles"] == ["config_links", "state_links"]

    def test_generation_manifest_absence_is_tolerated(self) -> None:
        tasks = _tasks("state_links")
        assert_task = next(
            task
            for task in tasks
            if task.get("name")
            == "Assert the stable consumer links resolve once a generation is committed"
        )
        assert "state_links_generation_manifest.stat.exists | default(false)" in str(
            assert_task["when"]
        )
        stat = next(
            task
            for task in tasks
            if task.get("name") == "Stat the committed generation manifest"
        )
        assert _module(stat)["path"] == (
            "{{ state_links_state_current_dir }}/manifest.json"
        )


class TestVerifyGenerationLayout:
    def test_verify_expects_contracts_v0110_generation(self) -> None:
        data = _vars("verify")
        assert data["verify_generation_contract_tag"] == "v0.12.0"
        assert data["verify_generation_manifest_version"] == 3
        assert data["verify_state_generation_manifest"] == (
            "{{ verify_state_current_dir }}/manifest.json"
        )
        assert data["verify_state_current_palette_dir"] == (
            "{{ verify_state_current_dir }}/palette"
        )
        assert data["verify_generation_tokens_path"] == "appearance/tokens.json"

    def test_verify_asserts_manifest_identity_and_appearance_targets(self) -> None:
        task = _task("Assert the generation manifest is one complete v3 generation")
        that = " ".join(str(item) for item in task["ansible.builtin.assert"]["that"])
        for expected in (
            "verify_generation_manifest.version == verify_generation_manifest_version",
            "generationHash is match('^[0-9a-f]{64}$')",
            "lnk_target | basename",
            "appearance.tokensPath == verify_generation_tokens_path",
            "appearance.targets | length > 0",
            "intent.mode == verify_generation_manifest.mode",
            "intent.skin == verify_generation_manifest.skin.name",
            "verify_generation_manifest.host is not defined",
            "verify_generation_manifest.host.source == 'hyprland'",
            "verify_generation_manifest.host.version == 1",
            "verify_generation_manifest.host.defaults | length > 0",
            "intent.host is defined",
            "verify_generation_artifacts",
            "verify_generation_artifact_expected_paths",
            "selectattr('format', 'in', ['rasi', 'conf', 'theme'])",
            "select('match', '.*[.]css$')",
            "verify_generation_artifact_checks.results | selectattr('stat.isreg')",
        ):
            assert expected in that, expected
        assert (
            "intent.host == verify_generation_manifest.host.fingerprint" in that
        )

    def test_verify_is_absent_tolerant_until_a_generation_is_committed(self) -> None:
        for name in (
            "Read the committed generation manifest",
            "Parse the committed generation manifest",
            "Build the expected non-CSS artifact paths",
            "Check the generation appearance targets exist when a generation is present",
            "Check the generation appearance artifacts exist when a generation is present",
            "Check the generation token document exists when a generation is present",
            "Assert the generation manifest is one complete v3 generation",
        ):
            task = _task(name)
            when = task.get("when")
            clauses = when if isinstance(when, list) else [when]
            assert "not ansible_check_mode" in clauses
            assert (
                "verify_generation_layout_checks.results[0].stat.exists | default(false)"
                in clauses
            ), name

    def test_verify_rejects_state_symlinks_into_app_tags(self) -> None:
        task = _task("Find state-root symlinks that point into an app tag")
        module = _module(task)
        assert module["argv"][-2] == "{{ verify_xdg_state_home | trim }}/dotfiles"
        assert module["argv"][-1] == "{{ verify_ags_apps_units_install_root }}"
        assert task["when"] == "not ansible_check_mode"
        assert "verify_state_tag_links.stdout" in str(
            _task("Assert the state root contains no symlink into an app tag")[
                "ansible.builtin.assert"
            ]["that"]
        )

    def test_verify_rejects_runtime_artifacts_inside_app_tags(self) -> None:
        data = _vars("verify")
        assert data["verify_app_tag_forbidden_runtime_artifacts"] == [
            "appearance.css",
            "skin.css",
            "skin.json",
            "tokens.json",
            "colors*",
        ]
        find = _task("Find runtime artifacts inside immutable app tags")
        module = _module(find)
        assert module["paths"] == "{{ verify_ags_apps_units_install_root }}"
        assert module["patterns"] == "{{ verify_app_tag_forbidden_runtime_artifacts }}"
        assert module["recurse"] is True
        assert module["hidden"] is True
        assert module["file_type"] == "any"
        assert "verify_app_tag_runtime_artifacts.matched" in str(
            _task("Assert no runtime artifact exists inside an immutable app tag")[
                "ansible.builtin.assert"
            ]["that"]
        )

    def test_wlogout_reads_the_generation_palette_directly(self) -> None:
        data = _vars("wlogout_config")
        assert data["wlogout_config_state_palette_file"] == (
            "{{ wlogout_config_state_root | trim }}/dotfiles/current/palette/colors.gtk.css"
        )
        tasks = (_ROLES_DIR / "wlogout_config" / "tasks" / "main.yml").read_text()
        assert "config/ags/colors.css" not in tasks
        assert "wlogout_config_state_palette_file" in tasks


def _run_post_seed(install: Path, home: Path, config: Path, state: Path) -> subprocess.CompletedProcess[str]:
    ansible_playbook = shutil.which("ansible-playbook")
    if ansible_playbook is None:
        pytest.skip("ansible-playbook not installed")
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("ANSIBLE_", "XDG_", "UV_TOOL_"))
    }
    env.update(
        HOME=str(home),
        XDG_CONFIG_HOME=str(config),
        XDG_STATE_HOME=str(state),
        ANSIBLE_CONFIG=str(_ANSIBLE_DIR / "ansible.cfg"),
    )
    return subprocess.run(
        [
            ansible_playbook,
            str(_ANSIBLE_DIR / "playbooks" / "config-links-post-seed.yaml"),
            "-e",
            f"install_dir={install}",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
    )


def _stage_palette(state: Path, *, manifest: bool) -> None:
    palette = state / "dotfiles" / "current" / "palette"
    palette.mkdir(parents=True, exist_ok=True)
    for name in (
        "colors.gtk.css",
        "colors.adw.css",
        "colors.rasi",
        "colors.btop.theme",
    ):
        (palette / name).write_text("/* palette */\n", encoding="utf-8")
    appearance = state / "dotfiles" / "current" / "appearance"
    appearance.mkdir(parents=True, exist_ok=True)
    for name in ("wlogout.css", "gtk3.css", "gtk4.css"):
        (appearance / name).write_text("/* appearance */\n", encoding="utf-8")
    (appearance / "rofi.rasi").write_text(
        "* { surface: transparent; }\n", encoding="utf-8"
    )
    (appearance / "kitty.conf").write_text(
        "font_family monospace\n", encoding="utf-8"
    )
    if manifest:
        (state / "dotfiles" / "current" / "manifest.json").write_text(
            '{"version": 3}\n', encoding="utf-8"
        )


class TestStableLinksExecution:
    def test_post_seed_creates_stable_links_outside_app_tags(self, tmp_path: Path) -> None:
        install = tmp_path / "install"
        home = tmp_path / "home"
        config = tmp_path / "config"
        state = tmp_path / "state"
        for path in (home, config, state):
            path.mkdir()
        for spine in (
            "gtk-3.0",
            "gtk-4.0",
            "rofi",
            "btop/themes",
            "wlogout",
            "kitty",
        ):
            (install / "config" / spine).mkdir(parents=True)
        _stage_palette(state, manifest=True)

        result = _run_post_seed(install, home, config, state)
        assert result.returncode == 0, result.stdout + result.stderr
        expected = {
            "gtk-3.0/colors.css": ("palette", "colors.gtk.css"),
            "gtk-4.0/colors.css": ("palette", "colors.adw.css"),
            "rofi/colors.rasi": ("palette", "colors.rasi"),
            "btop/themes/colors.btop.theme": ("palette", "colors.btop.theme"),
            "wlogout/appearance.css": ("appearance", "wlogout.css"),
            "gtk-3.0/appearance.css": ("appearance", "gtk3.css"),
            "gtk-4.0/appearance.css": ("appearance", "gtk4.css"),
            "rofi/appearance.rasi": ("appearance", "rofi.rasi"),
            "kitty/appearance.conf": ("appearance", "kitty.conf"),
        }
        for spine, (base, target) in expected.items():
            link = install / "config" / spine
            assert link.is_symlink(), spine
            assert os.readlink(link) == str(
                state / "dotfiles" / "current" / base / target
            )
            assert link.resolve().is_file(), spine
            assert not str(link.resolve()).startswith(str(install / "apps")), spine
            assert "generations" not in os.readlink(link), spine

    def test_post_seed_replaces_the_wlogout_fallback_with_the_stable_link(
        self, tmp_path: Path
    ) -> None:
        install = tmp_path / "install"
        home = tmp_path / "home"
        config = tmp_path / "config"
        state = tmp_path / "state"
        for path in (home, config, state):
            path.mkdir()
        for spine in (
            "gtk-3.0",
            "gtk-4.0",
            "rofi",
            "btop/themes",
            "wlogout",
            "kitty",
        ):
            (install / "config" / spine).mkdir(parents=True)
        fallback = install / "config" / "wlogout" / "appearance.css"
        fallback.write_text("/* provisioning fallback, must not survive a seed */\n")
        _stage_palette(state, manifest=True)

        result = _run_post_seed(install, home, config, state)
        assert result.returncode == 0, result.stdout + result.stderr
        assert fallback.is_symlink(), "state_links must replace the regular fallback"
        assert os.readlink(fallback) == str(
            state / "dotfiles" / "current" / "appearance" / "wlogout.css"
        )
        assert fallback.read_text() == "/* appearance */\n", (
            "no stale fallback content may remain after the seed"
        )

    def test_post_seed_tolerates_a_fresh_state_root(self, tmp_path: Path) -> None:
        install = tmp_path / "install"
        home = tmp_path / "home"
        config = tmp_path / "config"
        state = tmp_path / "state"
        for path in (home, config, state):
            path.mkdir()
        for spine in (
            "gtk-3.0",
            "gtk-4.0",
            "rofi",
            "btop/themes",
            "wlogout",
            "kitty",
        ):
            (install / "config" / spine).mkdir(parents=True)

        result = _run_post_seed(install, home, config, state)
        assert result.returncode == 0, result.stdout + result.stderr
        # Links are still provisioned; they resolve only after the seed commits
        # a generation. Absence of the generation is not a provisioning failure.
        for spine in (
            "gtk-3.0/colors.css",
            "gtk-4.0/colors.css",
            "rofi/colors.rasi",
            "btop/themes/colors.btop.theme",
            "wlogout/appearance.css",
            "gtk-3.0/appearance.css",
            "gtk-4.0/appearance.css",
            "rofi/appearance.rasi",
            "kitty/appearance.conf",
        ):
            assert (install / "config" / spine).is_symlink(), spine


_CONTRACTS_FIXTURE = (
    Path(__file__).resolve().parent.parent / "fixtures" / "contracts" / "v0.12.0"
)


class TestVendoredContractsV0120:
    """The engine vendors the v0.12.0 generation/appearance schemas it validates."""

    def test_pin_names_contracts_v0120_and_matches_every_schema_digest(self) -> None:
        pin = (_CONTRACTS_FIXTURE / "PIN").read_text()
        assert "contracts=v0.12.0" in pin
        import hashlib

        for schema in _CONTRACTS_FIXTURE.glob("*.schema.json"):
            digest = hashlib.sha256(schema.read_bytes()).hexdigest()
            assert f"sha256 {digest} {schema.name}" in pin, schema.name

    def test_generation_manifest_schema_is_the_v3_shape(self) -> None:
        import json

        schema = json.loads(
            (_CONTRACTS_FIXTURE / "generation-manifest.schema.json").read_text()
        )
        assert schema["properties"]["version"]["const"] == 3
        required = set(schema["required"])
        assert {
            "version",
            "generationHash",
            "created",
            "committed",
            "layers",
            "skin",
            "appearance",
            "mode",
            "intent",
            "source",
        } <= required
        assert schema["additionalProperties"] is False
        assert schema["definitions"]["hash"]["pattern"] == "^[0-9a-f]{64}$"
        appearance = schema["definitions"]["appearance"]
        assert "appearance/tokens.json" in str(appearance)
        assert "appearance/[a-z0-9]" in str(schema["definitions"]["target"])

    def test_generation_manifest_schema_adds_optional_css_free_artifacts(self) -> None:
        import json

        schema = json.loads(
            (_CONTRACTS_FIXTURE / "generation-manifest.schema.json").read_text()
        )
        artifact = schema["definitions"]["artifact"]
        assert set(artifact["required"]) == {"consumer", "path", "format"}
        assert artifact["properties"]["format"]["enum"] == ["rasi", "conf", "theme"]
        assert "css" not in artifact["properties"]["format"]["enum"]
        appearance = schema["definitions"]["appearance"]
        assert "artifacts" not in appearance["required"]
        artifacts = appearance["properties"]["artifacts"]
        assert artifacts["items"]["$ref"] == "#/definitions/artifact"
        assert artifacts["minItems"] == 1
        assert artifacts["uniqueItems"] is True

    def test_artifacts_rasi_manifest_fixture_is_non_css(self) -> None:
        import json

        manifest = json.loads(
            (
                _CONTRACTS_FIXTURE
                / "generation-manifest-artifacts.rasi.valid.json"
            ).read_text()
        )
        artifacts = manifest["appearance"]["artifacts"]
        assert artifacts == [
            {
                "consumer": "rofi",
                "path": "appearance/rofi.rasi",
                "format": "rasi",
            }
        ]
        assert not any(item["path"].endswith(".css") for item in artifacts)

    def test_generation_manifest_schema_accepts_an_optional_host_block(self) -> None:
        import json

        schema = json.loads(
            (_CONTRACTS_FIXTURE / "generation-manifest.schema.json").read_text()
        )
        host = schema["definitions"]["host"]
        assert set(host["required"]) == {
            "source",
            "version",
            "fingerprint",
            "defaults",
        }
        assert host["properties"]["source"]["enum"] == ["hyprland"]
        assert host["properties"]["version"]["const"] == 1
        assert host["properties"]["fingerprint"]["$ref"].endswith("/hash")
        assert host["properties"]["defaults"]["minProperties"] == 1
        assert "host" not in schema["required"]
        assert schema["allOf"], "host/intent.host coupling must stay explicit"

    def test_host_bearing_manifest_fixture_carries_a_matching_intent_host(self) -> None:
        import json

        manifest = json.loads(
            (
                _CONTRACTS_FIXTURE / "generation-manifest-host.valid.json"
            ).read_text()
        )
        assert manifest["version"] == 3
        assert manifest["host"]["source"] == "hyprland"
        assert manifest["host"]["version"] == 1
        assert manifest["host"]["defaults"]
        assert manifest["intent"]["host"] == manifest["host"]["fingerprint"]

    def test_generation_manifest_schema_accepts_rectangle_host_radii(self) -> None:
        """contracts v0.12.0 delegates window/panel geometry plus card/control/cell radii."""
        import json

        schema = json.loads(
            (_CONTRACTS_FIXTURE / "generation-manifest.schema.json").read_text()
        )
        defaults = schema["definitions"]["host"]["properties"]["defaults"]
        assert set(defaults["properties"]) == {
            "surface.window.radius",
            "surface.window.border-width",
            "surface.panel.radius",
            "surface.panel.border-width",
            "surface.card.radius",
            "surface.control.radius",
            "surface.cell.radius",
        }
        for path in (
            "surface.window.radius",
            "surface.panel.radius",
            "surface.card.radius",
            "surface.control.radius",
            "surface.cell.radius",
        ):
            assert defaults["properties"][path]["maximum"] == 64
        for path in ("surface.window.border-width", "surface.panel.border-width"):
            assert defaults["properties"][path]["maximum"] == 16
        assert "surface.pill.radius" not in defaults["properties"]
        assert "surface.window.padding" not in defaults["properties"]
        assert "surface.window.opacity" not in defaults["properties"]

    def test_host_rectangle_manifest_fixture_records_all_five_paths(self) -> None:
        import json

        manifest = json.loads(
            (
                _CONTRACTS_FIXTURE / "generation-manifest-host-rectangles.valid.json"
            ).read_text()
        )
        assert manifest["host"]["defaults"] == {
            "surface.panel.radius": 0,
            "surface.panel.border-width": 1,
            "surface.card.radius": 0,
            "surface.control.radius": 0,
            "surface.cell.radius": 0,
        }
        assert "surface.pill.radius" not in manifest["host"]["defaults"]
        assert manifest["intent"]["host"] == manifest["host"]["fingerprint"]

    def test_host_window_manifest_records_the_window_defaults(self) -> None:
        """contracts v0.12.0 adds the required window role and its host paths."""
        import json

        manifest = json.loads(
            (
                _CONTRACTS_FIXTURE / "generation-manifest-host-window.valid.json"
            ).read_text()
        )
        assert manifest["host"]["defaults"] == {
            "surface.window.radius": 12,
            "surface.window.border-width": 1.5,
            "surface.panel.radius": 0,
            "surface.panel.border-width": 1,
        }
        assert "surface.window.opacity" not in manifest["host"]["defaults"]
        assert "surface.window.padding" not in manifest["host"]["defaults"]

    def test_pill_radius_host_default_fixture_is_not_delegable(self) -> None:
        import json

        manifest = json.loads(
            (
                _CONTRACTS_FIXTURE / "generation-manifest-host-pill-default.invalid.json"
            ).read_text()
        )
        schema = json.loads(
            (_CONTRACTS_FIXTURE / "generation-manifest.schema.json").read_text()
        )
        allowed = schema["definitions"]["host"]["properties"]["defaults"]["properties"]
        assert "surface.pill.radius" in manifest["host"]["defaults"]
        assert "surface.pill.radius" not in allowed

    def test_appearance_manifest_schema_requires_window_and_opacity(self) -> None:
        """contracts v0.12.0: six required surface roles with a unitless
        [0,1] window opacity; window is never an alias of panel."""
        import json

        schema = json.loads(
            (_CONTRACTS_FIXTURE / "appearance-manifest.schema.json").read_text()
        )
        assert schema["definitions"]["surfaceGroup"]["required"] == [
            "window",
            "panel",
            "card",
            "cell",
            "control",
            "pill",
        ]
        window = schema["definitions"]["windowRole"]
        assert set(window["required"]) == {
            "bg",
            "border",
            "border-width",
            "radius",
            "padding",
            "shadow",
            "blur",
            "opacity",
        }
        opacity = schema["definitions"]["opacityValue"]
        assert opacity["type"] == "number"
        assert opacity["minimum"] == 0
        assert opacity["maximum"] == 1
        inherit = schema["definitions"]["hostPolicy"]["properties"]["inherit"]
        assert inherit["items"]["enum"] == [
            "surface.window.radius",
            "surface.window.border-width",
            "surface.panel.radius",
            "surface.panel.border-width",
            "surface.card.radius",
            "surface.control.radius",
            "surface.cell.radius",
        ]

    def test_appearance_window_fixtures_cover_the_required_role(self) -> None:
        """The vendored window fixtures pin acceptance and rejection."""
        import json

        glass = json.loads(
            (_CONTRACTS_FIXTURE / "appearance-manifest-glass.valid.json").read_text()
        )
        window = glass["groups"]["surface"]["window"]
        assert set(window) == {
            "bg",
            "border",
            "border-width",
            "radius",
            "padding",
            "shadow",
            "blur",
            "opacity",
        }
        assert 0 <= window["opacity"] <= 1
        missing = json.loads(
            (
                _CONTRACTS_FIXTURE
                / "appearance-manifest-missing-window.invalid.json"
            ).read_text()
        )
        assert "window" not in missing["groups"]["surface"]
        too_large = json.loads(
            (
                _CONTRACTS_FIXTURE
                / "appearance-manifest-opacity-too-large.invalid.json"
            ).read_text()
        )
        assert too_large["groups"]["surface"]["window"]["opacity"] > 1

    def test_v2_boolean_ack_is_not_a_contract_shape(self) -> None:
        import json

        schema = json.loads(
            (_CONTRACTS_FIXTURE / "appearance-refresh-result.schema.json").read_text()
        )
        definitions = schema["definitions"]
        assert set(definitions) == {"genHash", "reason", "applied", "deferred", "failed"}
        assert definitions["applied"]["required"] == ["applied"]
        assert definitions["deferred"]["required"] == ["deferred", "genHash"]
        assert definitions["failed"]["required"] == ["failed", "retryable", "genHash"]
        assert '"ok"' not in json.dumps(schema)
