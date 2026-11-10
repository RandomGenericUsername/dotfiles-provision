#!/usr/bin/env python3
"""Pin-only preflight: every engine mirror must match the composition fixture.

This is deliberately narrow: it catches stale asset/contract/platform tags in
role vars and the fixture tuple before a pin-only release enters the (much more
expensive) full gates. It does not replace the full gates for behavior changes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/composition/dotfiles/provisioning"


def _load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _role_vars() -> list[tuple[Path, dict[str, Any]]]:
    found: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted((ROOT / "ansible/roles").glob("*/vars/main.yml")):
        data = _load(path)
        if isinstance(data, dict):
            found.append((path, data))
    return found


def main() -> int:
    assets = _load(FIXTURE / "assets.yaml")
    tuple_data = _load(FIXTURE / "program-tuple.yaml")
    apps = _load(FIXTURE / "apps.yaml")
    assets_tag = str(assets["assets"]["tag"])
    contracts_tag = str(tuple_data["contracts"])
    platform_tag = str(tuple_data["ags-platform"])
    errors: list[str] = []
    if str(tuple_data["dotfiles-assets"]) != assets_tag:
        errors.append(
            "program-tuple dotfiles-assets="
            f"{tuple_data['dotfiles-assets']!r}, expected {assets_tag!r}"
        )

    for path, data in _role_vars():
        rel = path.relative_to(ROOT)
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
        "bar": "v0.6.1",
        "notifications": "v0.5.1",
        "capture": "v0.7.1",
        "clipboard": "v0.6.1",
        "wallpaper-selector": "v0.5.1",
        "icme": "v0.5.1",
        "btop-theme-studio": "v0.5.1",
    }
    fixture_apps = _load(
        ROOT / "tests/fixtures/ags-apps/app-list/all-standalone.apps.yaml"
    )
    by_app = {str(item["app"]): str(item["tag"]) for item in fixture_apps["apps"]}
    if by_app != expected_app_tags:
        errors.append(
            "all-standalone fixture app tags differ: "
            f"got {by_app!r}, expected {expected_app_tags!r}"
        )
    if apps.get("apps") is None:
        errors.append(f"{FIXTURE / 'apps.yaml'}: missing apps list")

    if errors:
        print("pin-audit: FAIL", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(
        "pin-audit: PASS "
        f"(assets={assets_tag}, contracts={contracts_tag}, platform={platform_tag}, "
        f"apps={len(expected_app_tags)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
