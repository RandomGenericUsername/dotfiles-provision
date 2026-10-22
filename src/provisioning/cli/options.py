"""Shared option definitions for the dotfiles-provision CLI.

Module-level importable constants (no eager ``create_renderer``) so the
composition root in ``main.py`` stays the single place that wires renderers
and dependencies. Only ``typer`` and ``cli_output`` are imported — both are
declared package dependencies and layering-guard-allowed roots.
"""

from __future__ import annotations

from pathlib import Path

import typer
from cli_output.domain.enums import OutputFormat

OUTPUT_FORMAT_OPT: OutputFormat = typer.Option(
    OutputFormat.JSON,
    "--output-format",
    help="Output format for command results",
    case_sensitive=False,
)

CHECK_OPT: bool = typer.Option(
    False,
    "--check",
    help="Dry run: complete cleanly with no mutation",
)

BECOME_PASSWORD_OPT: str | None = typer.Option(
    None,
    "--become-password",
    help="Sudo password for become:true plays (packages/bootstrap); input is hidden",
    hide_input=True,
)

ASK_BECOME_PASS_OPT: bool = typer.Option(
    False,
    "--ask-become-pass",
    help="Prompt interactively for the sudo become password (hidden input, "
    "like ansible-playbook -K)",
)

EXPECTED_ENGINE_TAG_OPT: str | None = typer.Option(
    None,
    "--expected-engine-tag",
    help="Assert the installed engine reports this tag (the composition's "
    "installer.pin, e.g. v0.1.1). Default: no engine assertion.",
    metavar="TAG",
)

# ── Composition seam (AD-17) ───────────────────────────────────────────────
# The engine repo owns the Ansible tree; the composition repo owns the
# manifests and the runtime source. These two options are the ONLY way the
# engine learns where the composition is: no role derives a path from
# `playbook_dir` (a pinned engine checkout has no composition ancestors).
#
# `--manifests-dir` defaults to `<cwd>/dotfiles/provisioning` (the documented
# layout of a composition checkout). `--composition-root` defaults to the
# manifests dir's grandparent (`<composition>/dotfiles/provisioning` ->
# `<composition>`); pass it explicitly when the manifests live elsewhere.
MANIFESTS_DIR_OPT: Path | None = typer.Option(
    None,
    "--manifests-dir",
    help="The composition repo's manifest directory (dotfiles/provisioning/). "
    "Default: <cwd>/dotfiles/provisioning",
    metavar="PATH",
)

COMPOSITION_ROOT_OPT: Path | None = typer.Option(
    None,
    "--composition-root",
    help="The composition repo checkout root (holds dotfiles/ and src/runtime/). "
    "Default: the parent of --manifests-dir's parent",
    metavar="PATH",
)

INVENTORY_OPT: Path | None = typer.Option(
    None,
    "--inventory",
    help="Ansible inventory to run against. Default: this engine's "
    "ansible/inventory/localhost.yaml",
    metavar="PATH",
)
