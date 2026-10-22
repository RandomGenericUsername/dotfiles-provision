"""Shared test fixtures for the installer engine.

The engine repo owns the Ansible tree but **not** the composition checkout:
`dotfiles/provisioning/*.yaml` (the manifests), `dotfiles/provisioning/scripts/`
and `dotfiles/config/btop/active-theme` are the composition repo's, and
`src/runtime/` is the composition's runtime. A unit test in this repo therefore
cannot walk up to a real composition tree — there is none above an engine
checkout.

Resolution order for tests:

1. ``$DOTFILES_COMPOSITION_ROOT`` — an explicit composition checkout. Point it
   at a real ``dotfiles-v3`` to check the engine mirrors against live
   manifests instead of the fixture.
2. ``tests/fixtures/composition/`` — a minimal composition tree copied from
   ``dotfiles-v3`` when the engine was extracted (the five manifests, the
   gloview-activate script, ``btop/active-theme`` and a runtime stub).

The fixture is a **test input**, never a deployed source: production reads only
what ``dotfiles-provision --manifests-dir/--composition-root`` resolves.
"""

from __future__ import annotations

import os
from pathlib import Path

#: `<engine repo>/tests/support.py` -> `<engine repo>`
ENGINE_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_COMPOSITION = Path(__file__).resolve().parent / "fixtures" / "composition"


def composition_root() -> Path:
    """Return the composition checkout the tests read manifests from."""
    override = os.environ.get("DOTFILES_COMPOSITION_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return FIXTURE_COMPOSITION


def manifests_dir() -> Path:
    """Return the composition's manifest directory (``dotfiles/provisioning/``)."""
    return composition_root() / "dotfiles" / "provisioning"


def manifest(name: str) -> Path:
    """Return one manifest path by file name (e.g. ``assets.yaml``)."""
    return manifests_dir() / name


def composition_file(*parts: str) -> Path:
    """Return a path under the composition checkout root."""
    return composition_root().joinpath(*parts)


__all__ = [
    "ENGINE_ROOT",
    "FIXTURE_COMPOSITION",
    "composition_file",
    "composition_root",
    "manifest",
    "manifests_dir",
]
