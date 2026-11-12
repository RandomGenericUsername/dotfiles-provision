#!/usr/bin/env python3
"""Pin-only preflight: every engine mirror must match the composition fixture.

This is deliberately narrow: it catches stale asset/contract/platform tags in
role vars and the fixture tuple before a pin-only release enters the (much more
expensive) full gates. It does not replace the full gates for behavior changes.

Skin consumer coverage is structural, not a schema validator: the deployed
skin plane must name exactly the released five manifests, the ten
`<configDir>.gtk.css.j2` CSS targets and the rofi `rasi` / kitty `conf`
artifacts (twelve templates in total). In particular, `terminal-host`, `gtk3`,
`gtk4`, the rofi artifact and the kitty artifact are part of the v0.20.2
release and must not silently drop out of `verify` again.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

# Released dotfiles-assets v0.20.2 skin plane. Keep these ordered sets explicit:
# the audit is a pin/structural check, so a missing or extra name is a drift.
EXPECTED_SKIN_MANIFEST_NAMES = (
    "glass",
    "flat",
    "paper",
    "terminal",
    "terminal-host",
)
EXPECTED_SKIN_TARGET_FILES = (
    "ags.gtk.css.j2",
    "ags-clipboard.gtk.css.j2",
    "ags-notifications.gtk.css.j2",
    "ags-wallpaper-selector.gtk.css.j2",
    "ags-capture.gtk.css.j2",
    "ags-icme.gtk.css.j2",
    "ags-btop-studio.gtk.css.j2",
    "gtk3.gtk.css.j2",
    "gtk4.gtk.css.j2",
    "wlogout.gtk.css.j2",
)
EXPECTED_SKIN_ARTIFACT_FILES = ("rofi.rasi.j2", "kitty.conf.j2")


def _fixture(root: Path) -> Path:
    return root / "tests/fixtures/composition/dotfiles/provisioning"


def _load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _role_vars(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    found: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted((root / "ansible/roles").glob("*/vars/main.yml")):
        data = _load(path)
        if isinstance(data, dict):
            found.append((path, data))
    return found


def _verify_vars(root: Path) -> dict[str, Any]:
    data = _load(root / "ansible/roles/verify/vars/main.yml")
    if not isinstance(data, dict):
        raise SystemExit("ansible/roles/verify/vars/main.yml must be a mapping")
    return data


def _skin_plane_errors(root: Path) -> list[str]:
    """Check the released manifest names and consumer-target set exactly.

    This intentionally checks names only. The deployed skin payload is
    validated by `verify`; a pin audit must stay cheap and structural.
    """
    verify_vars = _verify_vars(root)
    errors: list[str] = []

    manifest_names = [
        str(name) for name in verify_vars.get("verify_skins_manifest_names", [])
    ]
    expected_manifests = list(EXPECTED_SKIN_MANIFEST_NAMES)
    if len(manifest_names) != len(expected_manifests) or set(manifest_names) != set(
        expected_manifests
    ):
        errors.append(
            "verify_skins_manifest_names="
            f"{manifest_names!r}, expected exactly {expected_manifests!r} "
            "(glass, flat, paper, terminal, terminal-host)"
        )

    target_files = [
        str(name) for name in verify_vars.get("verify_skins_template_files", [])
    ]
    expected_targets = list(EXPECTED_SKIN_TARGET_FILES)
    if len(target_files) != len(expected_targets) or set(target_files) != set(
        expected_targets
    ):
        errors.append(
            "verify_skins_template_files="
            f"{target_files!r}, expected exactly the ten released CSS targets "
            f"{expected_targets!r}"
        )

    artifact_files = [
        str(name) for name in verify_vars.get("verify_skins_artifact_files", [])
    ]
    expected_artifacts = list(EXPECTED_SKIN_ARTIFACT_FILES)
    if len(artifact_files) != len(expected_artifacts) or set(artifact_files) != set(
        expected_artifacts
    ):
        errors.append(
            "verify_skins_artifact_files="
            f"{artifact_files!r}, expected exactly the released non-CSS artifacts "
            f"{expected_artifacts!r}"
        )

    return errors


def audit(root: Path = ROOT) -> tuple[list[str], dict[str, str | int]]:
    fixture = _fixture(root)
    assets = _load(fixture / "assets.yaml")
    tuple_data = _load(fixture / "program-tuple.yaml")
    apps = _load(fixture / "apps.yaml")
    assets_tag = str(assets["assets"]["tag"])
    contracts_tag = str(tuple_data["contracts"])
    platform_tag = str(tuple_data["ags-platform"])
    errors: list[str] = []
    if str(tuple_data["dotfiles-assets"]) != assets_tag:
        errors.append(
            "program-tuple dotfiles-assets="
            f"{tuple_data['dotfiles-assets']!r}, expected {assets_tag!r}"
        )

    for path, data in _role_vars(root):
        rel = path.relative_to(root)
        for key, value in data.items():
            if not isinstance(value, str):
                continue
            if key.endswith("_assets_pinned_tag") and value != assets_tag:
                errors.append(f"{rel}: {key}={value!r}, expected {assets_tag!r}")
            if key in {
                "verify_generation_contract_tag",
                "verify_skins_expected_contract_tag",
            } and value != contracts_tag:
                errors.append(f"{rel}: {key}={value!r}, expected {contracts_tag!r}")
            if key == "ags_platform_version" and value != platform_tag:
                errors.append(f"{rel}: {key}={value!r}, expected {platform_tag!r}")

    # The all-standalone fixture is the canonical final app inventory.
    expected_app_tags = {
        "bar": "v0.6.9",
        "notifications": "v0.5.2",
        "capture": "v0.7.2",
        "clipboard": "v0.6.2",
        "wallpaper-selector": "v0.5.2",
        "icme": "v0.5.2",
        "btop-theme-studio": "v0.5.2",
    }
    fixture_apps = _load(
        root / "tests/fixtures/ags-apps/app-list/all-standalone.apps.yaml"
    )
    by_app = {str(item["app"]): str(item["tag"]) for item in fixture_apps["apps"]}
    if by_app != expected_app_tags:
        errors.append(
            "all-standalone fixture app tags differ: "
            f"got {by_app!r}, expected {expected_app_tags!r}"
        )
    if apps.get("apps") is None:
        errors.append(f"{fixture / 'apps.yaml'}: missing apps list")

    errors.extend(_skin_plane_errors(root))

    summary: dict[str, str | int] = {
        "assets": assets_tag,
        "contracts": contracts_tag,
        "platform": platform_tag,
        "apps": len(expected_app_tags),
        "skins": len(EXPECTED_SKIN_MANIFEST_NAMES),
        "targets": len(EXPECTED_SKIN_TARGET_FILES),
        "artifacts": len(EXPECTED_SKIN_ARTIFACT_FILES),
    }
    return errors, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="repo root to audit (defaults to this script's checkout)",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    errors, summary = audit(root)
    if errors:
        print("pin-audit: FAIL", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(
        "pin-audit: PASS "
        f"(assets={summary['assets']}, contracts={summary['contracts']}, "
        f"platform={summary['platform']}, apps={summary['apps']}, "
        f"skins={summary['skins']}, targets={summary['targets']}, "
        f"artifacts={summary['artifacts']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
