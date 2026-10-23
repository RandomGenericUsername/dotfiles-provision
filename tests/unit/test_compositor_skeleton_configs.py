from __future__ import annotations

import yaml

from tests.support import ENGINE_ROOT, composition_root, manifests_dir

# S2: the static config corpus is NOT authored in this checkout any more — it
# ships in the pinned `dotfiles-assets` repo (`configs/` class) and the
# compositor_configs / config_copies roles read the checkout. The old
# byte-level assertions of this module (dofile wiring, hyprpaper's exact lines,
# the session PATH prepend) had the repo files as their subject; that subject
# moved with the bytes, so what remains here is the CONSUMER contract that no
# single role test states on its own:
#
#   1. every config source in both roles is the pinned checkout, at the tag the
#      assets manifest declares (no role-local pin drift, no repo tree);
#   2. the 15 compositor skeletons are exactly the configs-class files the
#      consumer addresses (an unregistered file silently never deploys);
#   3. the in-tree static corpus is gone, and since R-07 so is the mutable
#      `btop/active-theme`: `dotfiles/config/` itself must not exist.
#
# The corpus's own content checks now belong to the assets repo (configs/README.md
# and the release acceptance grep); a consumer-side byte test would have to fetch
# the tag, which this suite deliberately does not do.


_REPO_ROOT = composition_root()
_MANIFESTS = manifests_dir()
_ANSIBLE_DIR = ENGINE_ROOT / "ansible"
_ROLES_DIR = _ANSIBLE_DIR / "roles"
_CONFIG_DIR = _REPO_ROOT / "dotfiles" / "config"


def _vars(role: str) -> dict[str, object]:
    data = yaml.safe_load((_ROLES_DIR / role / "vars" / "main.yml").read_text())
    assert isinstance(data, dict)
    return data


def _assets_tag() -> str:
    manifest = yaml.safe_load(
        (_MANIFESTS / "assets.yaml").read_text()
    )
    return str(manifest["assets"]["tag"])


#: The 15 non-bar compositor skeletons, relative to the assets `configs/` class.
_EXPECTED_COMPOSITOR_FILES = {
    "hypr/animations.lua",
    "hypr/autostart.lua",
    "hypr/colors.lua",
    "hypr/cursor.lua",
    "hypr/decoration.lua",
    "hypr/env-variables.lua",
    "hypr/general.lua",
    "hypr/gloview.lua",
    "hypr/hyprland.lua",
    "hypr/input.lua",
    "hypr/keybindings.lua",
    "hypr/monitors.lua",
    "hypr/window-rules.lua",
    "hyprpaper/hyprpaper.conf",
    "rofi/launcher/config.rasi",
}

#: Retired in S2 (the copied corpus). wlogout retired in S3 with its last in-tree
#: file, the Jinja source — `test_wlogout_dir_is_gone` asserts that separately.
_RETIRED_CONFIG_TREES = ("hypr", "hyprpaper", "nvim", "rofi", "starship")


class TestConfigCorpusPin:
    def test_compositor_sources_are_the_pinned_configs_class(self) -> None:
        data = _vars("compositor_configs")
        tag = _assets_tag()
        assert str(data["compositor_configs_assets_pinned_tag"]) == tag, (
            "the compositor config pin must equal dotfiles/provisioning/assets.yaml "
            "`assets.tag` — a role-local pin drifts silently"
        )
        prefix = (
            "{{ install_dir | trim }}/assets/"
            "{{ compositor_configs_assets_pinned_tag }}/configs/"
        )
        assert str(data["compositor_configs_assets_configs_dir"]) == prefix.rstrip("/")
        relative = {
            str(entry["source"]).split("}}/", 1)[1]
            for entry in data["compositor_configs_skeleton_files"]
        }
        assert relative == _EXPECTED_COMPOSITOR_FILES, (
            "the 15 compositor skeletons must be exactly the configs-class files "
            f"the consumer addresses; diff={relative ^ _EXPECTED_COMPOSITOR_FILES}"
        )
        for entry in data["compositor_configs_skeleton_files"]:
            assert str(entry["source"]).startswith(
                "{{ compositor_configs_assets_configs_dir }}/"
            ), entry["source"]
            assert "dotfiles/config" not in str(entry["source"])

    def test_config_copy_sources_are_the_pinned_configs_class(self) -> None:
        data = _vars("config_copies")
        assert str(data["config_copies_assets_pinned_tag"]) == _assets_tag()
        prefix = (
            "{{ install_dir | trim }}/assets/"
            "{{ config_copies_assets_pinned_tag }}/configs/"
        )
        assert str(data["config_copies_assets_configs_dir"]) == prefix.rstrip("/")
        entries = {str(entry["name"]): dict(entry) for entry in data["config_copies_entries"]}
        assert set(entries) == {"nvim", "starship", "wlogout"}, (
            "the copy set is nvim, starship and wlogout (S2 dropped zsh — its only "
            "file was a template nothing read)"
        )
        assert entries["wlogout"].get("files") == ["layout"], (
            "wlogout is per-file: style.css is RENDERED by wlogout_config"
        )


class TestRetiredConfigCorpus:
    def test_static_config_dirs_are_gone(self) -> None:
        for name in _RETIRED_CONFIG_TREES:
            assert not (_CONFIG_DIR / name).exists(), (
                f"dotfiles/config/{name}/ still exists — the static corpus is the "
                "pinned dotfiles-assets repo (configs class)"
            )

    def test_wlogout_dir_is_gone(self) -> None:
        """S3: the wlogout directory's last in-tree file was its template source.

        `layout` shipped to the corpus in S2 and `style.css.tpl` in S3, so the
        directory has no remaining purpose here — its presence would be a
        half-retired tree (and a place for a stale `layout` to reappear).
        """
        assert not (_CONFIG_DIR / "wlogout").exists(), (
            "dotfiles/config/wlogout/ must be gone: `layout` is the pinned corpus's "
            "configs class and `style.css.tpl` is its templates class (S3)"
        )

    def test_composition_config_tree_is_gone(self) -> None:
        """R-07: the last file in `dotfiles/config/` (btop/active-theme) is now
        host state in the install spine, so the composition authors no config
        tree at all."""
        assert not _CONFIG_DIR.exists(), (
            "dotfiles/config/ must be absent: the static corpus is the pinned "
            "assets configs class, the templates are its templates class, and "
            "the active-theme preference is host state in the install spine "
            "(R-07/OPEN-5)"
        )

    def test_render_sources_are_the_pinned_templates_class(self) -> None:
        """S3 consumer contract: every rendering role reads
        `<install>/assets/<its pin>/templates/`, at the manifest's tag."""
        tag = _assets_tag()
        rendered: dict[str, str] = {}
        for role in (
            "zsh_config",
            "kitty_config",
            "btop_config",
            "wlogout_config",
            "display_manager",
        ):
            data = _vars(role)
            assert str(data[f"{role}_assets_pinned_tag"]) == tag, (
                f"{role}_assets_pinned_tag must equal the manifest tag {tag}"
            )
            assert str(data[f"{role}_assets_templates_dir"]) == (
                f"{{{{ install_dir | trim }}}}/assets/"
                f"{{{{ {role}_assets_pinned_tag }}}}/templates"
            )
            tasks = yaml.safe_load((_ROLES_DIR / role / "tasks" / "main.yml").read_text())
            for task in tasks:
                if not isinstance(task, dict):
                    continue
                body = task.get("ansible.builtin.template")
                if not isinstance(body, dict):
                    continue
                src = str(body.get("src", ""))
                assert src.startswith(f"{{{{ {role}_assets_templates_dir }}}}/"), (
                    f"{role} render src must read the pinned templates class; got {src!r}"
                )
                rendered[role] = src
        assert len(rendered) == 5, (
            f"expected one rendered source per role, got {sorted(rendered)}"
        )
