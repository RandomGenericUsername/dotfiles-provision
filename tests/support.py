"""Shared test fixtures for the installer engine.

The engine repo owns the Ansible tree but **not** the composition checkout:
`dotfiles/provisioning/*.yaml` (the manifests) and
`dotfiles/provisioning/scripts/` are the composition repo's; the runtime is the
pinned `dotfiles-runtime` repo. The btop active-theme preference is host state
in the install spine (R-07), not a composition file. A unit test in this repo
therefore cannot walk up to a real composition tree — there is none above an
engine checkout.

Resolution order for tests:

1. ``$DOTFILES_COMPOSITION_ROOT`` — an explicit composition checkout. Point it
   at a real ``dotfiles-v3`` to check the engine mirrors against live
   manifests instead of the fixture.
2. ``tests/fixtures/composition/`` — a minimal composition tree copied from
   ``dotfiles-v3`` when the engine was extracted (the five manifests and the
   gloview-activate script; the runtime is a pinned repo, not a stub).

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


def cli_tool_tags() -> dict[str, str]:
    """Return the composition's ``cli_tools_tags`` fact (name → tag).

    The ``cli_tools`` role resolves this mapping from
    ``dotfiles/provisioning/cli-tools.yaml`` and publishes it with ``set_fact``
    for the later bootstrap roles (REQ-014). Tests use the same composition
    manifest the role reads, so a fixture tag bump flows through every
    derivation assertion without a second edit.
    """
    import yaml

    loaded = yaml.safe_load(manifest("cli-tools.yaml").read_text())
    entries = loaded.get("entries") or []
    return {
        str(entry["name"]): str(entry["tag"])
        for entry in entries
        if entry.get("tag") is not None
    }


def render_pin(expression: object, *, tags: dict[str, str] | None = None, **context: object) -> str:
    """Render a role-var Jinja expression with a sample ``cli_tools_tags``.

    Role vars that used to carry a literal pin now read
    ``{{ cli_tools_tags.<name> }}`` (REQ-014). Asserting the raw string proves
    the source; rendering it with the composition's tags (or an explicit
    ``tags=`` sample) proves the resolved value a bootstrap would see.
    ``context`` supplies any other variable the expression references (e.g.
    ``install_dir``). ``regex_replace`` is Ansible's filter, not Jinja's, so it
    is registered here.
    """
    import re

    from jinja2 import Environment, StrictUndefined

    env = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
    env.filters["regex_replace"] = lambda value, pattern, repl: re.sub(
        pattern, repl, str(value)
    )
    values: dict[str, object] = {
        "cli_tools_tags": cli_tool_tags() if tags is None else dict(tags),
    }
    values.update(context)
    return env.from_string(str(expression)).render(**values)


__all__ = [
    "ENGINE_ROOT",
    "FIXTURE_COMPOSITION",
    "cli_tool_tags",
    "composition_file",
    "composition_root",
    "manifest",
    "manifests_dir",
    "render_pin",
]
