"""Typer CLI — the composition root (outer shell) of the provisioning hexagon.

This is the only production place that constructs ``AnsibleExecutor`` /
``AnsibleFactReader`` and wires them into the use cases. The callback resolves
the composition seam ONCE — ``--manifests-dir``, ``--composition-root`` and
``--inventory`` — and every command reuses it: no role derives a composition
path from ``playbook_dir`` (AD-17, installer engine).

The callback builds a ``CliDependencies`` bag on ``ctx.obj`` and every command
renders through the shared ``_render_run`` helper: ``ResultView`` on success
(including the resolved install dir), a structured ``ErrorView`` + non-zero
exit on the known adapter/domain errors or a failed run, and uncaught
propagation for anything unexpected.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path

import typer
from cli_output.adapters.factory import create_renderer
from cli_output.domain.enums import OutputFormat
from cli_output.domain.views import CustomView, ErrorView, ResultView
from cli_output.ports.renderer import Renderer

from provisioning.adapters.ansible_executor import (
    AnsibleExecutor,
    ProvisionExecutorError,
    ProvisionTimeoutError,
)
from provisioning.adapters.ansible_fact_reader import (
    AnsibleFactReader,
    InvalidFactOutputError,
    UnknownOsFamilyError,
)
from provisioning.adapters.yaml_manifest_reader import (
    ManifestReadError,
    YamlManifestReader,
)
from provisioning.application import (
    BootstrapUseCase,
    CompositionPathError,
    CompositionSeam,
    ProvisionMachineUseCase,
    VerifyCapabilityUseCase,
    resolve_install_dir,
)
from provisioning.cli.options import (
    ASK_BECOME_PASS_OPT,
    BECOME_PASSWORD_OPT,
    CHECK_OPT,
    COMPOSITION_ROOT_OPT,
    INVENTORY_OPT,
    MANIFESTS_DIR_OPT,
    OUTPUT_FORMAT_OPT,
)
from provisioning.domain.models import ProvisionResult

app = typer.Typer(
    name="dotfiles-provision",
    help=(
        "Dotfiles machine provisioning orchestrator.\n\n"
        "Establishes the operational environment (packages, CLI tools, assets, "
        "filesystem, settings, palette) that the Phase 2 runtime assumes exists.\n\n"
        "The engine owns the Ansible tree; the composition repo supplies the "
        "manifests and the runtime source. Point the engine at that composition "
        "with --manifests-dir (default: <cwd>/dotfiles/provisioning) and, when "
        "the layout differs, --composition-root.\n\n"
        "Commands:\n"
        "  plan       Diff desired machine state against actual state (Ansible --check)\n"
        "  apply      Apply provisioning idempotently\n"
        "  verify     Assert all done-criteria hold\n"
        "  bootstrap  Run the aggregate provisioning end-to-end\n"
        "  manifests  Resolve every manifest in --manifests-dir (read-only)"
    ),
)


@dataclass(frozen=True)
class EngineSettings:
    """Resolved engine input: the composition seam + the inventory to use.

    Both are resolved once by the CLI callback and threaded into every use
    case, so a run has one answer to "where is the composition?" and one
    inventory path.
    """

    seam: CompositionSeam
    inventory: Path


@dataclass
class CliDependencies:
    plan: ProvisionMachineUseCase
    apply: ProvisionMachineUseCase
    verify: VerifyCapabilityUseCase
    bootstrap: BootstrapUseCase


# main.py lives at src/provisioning/cli/main.py:
#   parents[0]=cli, parents[1]=provisioning, parents[2]=src, parents[3]=<engine repo>
_ANSIBLE_ROOT = Path(__file__).resolve().parents[3] / "ansible"


def default_inventory() -> Path:
    """The inventory shipped with this engine (local-connection localhost)."""
    return _ANSIBLE_ROOT / "inventory" / "localhost.yaml"


def build_deps(
    settings: EngineSettings | None = None,
    become_password: str | None = None,
) -> CliDependencies:
    """Wire the adapters and use cases.

    ``settings`` defaults to a cwd-resolved composition seam + this engine's
    inventory so tests and library callers keep a zero-argument entry point.
    The CLI always passes the callback-resolved settings explicitly.
    """
    resolved = (
        settings
        or EngineSettings(
            seam=CompositionSeam.resolve(), inventory=default_inventory()
        )
    )
    executor = AnsibleExecutor(
        inventory=resolved.inventory,
        tags="all",
        config_file=_ANSIBLE_ROOT / "ansible.cfg",
        become_password=become_password,
    )
    fact_reader = AnsibleFactReader()
    bootstrap_playbook = _ANSIBLE_ROOT / "playbooks" / "bootstrap.yaml"
    verify_playbook = _ANSIBLE_ROOT / "playbooks" / "verify.yaml"
    return CliDependencies(
        plan=ProvisionMachineUseCase(
            executor, fact_reader, bootstrap_playbook, seam=resolved.seam
        ),
        apply=ProvisionMachineUseCase(
            executor, fact_reader, bootstrap_playbook, seam=resolved.seam
        ),
        verify=VerifyCapabilityUseCase(executor, fact_reader, verify_playbook, seam=resolved.seam),
        bootstrap=BootstrapUseCase(executor, fact_reader, bootstrap_playbook, seam=resolved.seam),
    )


def _resolve_settings(
    renderer: Renderer,
    manifests_dir: Path | None,
    composition_root: Path | None,
    inventory: Path | None,
) -> EngineSettings:
    """Resolve and validate the engine's inputs, failing loud with a view.

    A bad path is a usage error, not an Ansible failure: resolving it here
    means a typo never reaches a playbook whose first task would otherwise
    copy from an empty path.
    """
    seam = CompositionSeam.resolve(
        manifests_dir=manifests_dir, composition_root=composition_root
    )
    resolved_inventory = (inventory or default_inventory()).expanduser().resolve()
    if not resolved_inventory.is_file():
        renderer.error(
            ErrorView(
                kind="InventoryPathError",
                message=(
                    f"--inventory is not a file: {resolved_inventory}. Pass the path to "
                    f"an Ansible inventory (the default is this engine's "
                    f"ansible/inventory/localhost.yaml)."
                ),
            )
        )
        raise typer.Exit(code=2) from None
    return EngineSettings(seam=seam, inventory=resolved_inventory)


@app.callback()
def main_callback(
    ctx: typer.Context,
    output_format: OutputFormat = OUTPUT_FORMAT_OPT,
    manifests_dir: Path | None = MANIFESTS_DIR_OPT,
    composition_root: Path | None = COMPOSITION_ROOT_OPT,
    inventory: Path | None = INVENTORY_OPT,
) -> None:
    renderer = create_renderer(output_format)
    ctx.obj = {
        "renderer": renderer,
        "settings": _resolve_settings(renderer, manifests_dir, composition_root, inventory),
    }


def _require_seam(ctx: typer.Context) -> EngineSettings:
    """Validate the composition seam before a command runs a playbook.

    Kept out of the callback so ``--help`` and ``version`` work outside a
    composition checkout; every command that reads the composition calls this
    first, so a bad path still fails before Ansible starts.
    """
    settings: EngineSettings = ctx.obj["settings"]
    try:
        settings.seam.validate()
    except CompositionPathError as exc:
        renderer: Renderer = ctx.obj["renderer"]
        renderer.error(ErrorView(kind="CompositionPathError", message=str(exc)))
        raise typer.Exit(code=2) from None
    return settings


def _render_run(
    renderer: Renderer,
    fn: Callable[[], ProvisionResult],
    command: str,
) -> None:
    try:
        result = fn()
    except (
        ProvisionExecutorError,
        ProvisionTimeoutError,
        UnknownOsFamilyError,
        InvalidFactOutputError,
    ) as exc:
        renderer.error(ErrorView(kind=type(exc).__name__, message=str(exc)))
        raise typer.Exit(code=1) from None
    if not result.success:
        details: dict[str, str] = {
            "stderr": result.stderr,
            "failed_tasks": [  # type: ignore[dict-item]
                label
                for label, status in result.tasks
                if status in ("failed", "unreachable")
            ],
        }
        if result.failure_detail:
            details["failure_detail"] = result.failure_detail
        if result.warnings:
            details["warnings"] = "\n".join(result.warnings)
        renderer.error(
            ErrorView(
                kind="ProvisionFailed",
                message=f"{command} failed (returncode={result.returncode})",
                details=details,
            )
        )
        raise typer.Exit(code=1) from None
    try:
        install_dir = str(resolve_install_dir())
    except (OSError, RuntimeError):
        install_dir = "unresolved"
    fields: dict[str, object] = {
        "command": command,
        "install_dir": install_dir,
        "returncode": result.returncode,
        "tasks": dict(result.tasks),
    }
    if result.warnings:
        fields["warnings"] = list(result.warnings)
    renderer.result(
        ResultView(
            success=True,
            title=command,
            fields=fields,
        )
    )


def _resolve_become_password(ask_become_pass: bool, become_password: str | None) -> str | None:
    """Resolve the become password: ``--ask-become-pass`` prompts interactively
    (hidden input, like ``ansible-playbook -K``); ``--become-password`` takes it
    as an argument. An explicit argument wins over the prompt."""
    if become_password is not None:
        return become_password
    if ask_become_pass:
        import getpass

        return getpass.getpass("BECOME password: ")
    return None


@app.command(help="Diff desired machine state against actual state (Ansible --check)")
def plan(
    ctx: typer.Context,
    ask_become_pass: bool = ASK_BECOME_PASS_OPT,
    become_password: str | None = BECOME_PASSWORD_OPT,
) -> None:
    deps = build_deps(
        _require_seam(ctx),
        become_password=_resolve_become_password(ask_become_pass, become_password),
    )
    renderer: Renderer = ctx.obj["renderer"]
    _render_run(renderer, lambda: deps.plan.provision(check=True), "plan")


@app.command(help="Apply provisioning idempotently")
def apply(
    ctx: typer.Context,
    ask_become_pass: bool = ASK_BECOME_PASS_OPT,
    become_password: str | None = BECOME_PASSWORD_OPT,
) -> None:
    deps = build_deps(
        _require_seam(ctx),
        become_password=_resolve_become_password(ask_become_pass, become_password),
    )
    renderer: Renderer = ctx.obj["renderer"]
    _render_run(renderer, lambda: deps.apply.provision(check=False), "apply")


@app.command(help="Assert all done-criteria hold")
def verify(ctx: typer.Context) -> None:
    deps = build_deps(_require_seam(ctx))
    renderer: Renderer = ctx.obj["renderer"]
    _render_run(renderer, lambda: deps.verify.verify(), "verify")


@app.command(help="Run the aggregate provisioning end-to-end")
def bootstrap(
    ctx: typer.Context,
    check: bool = CHECK_OPT,
    ask_become_pass: bool = ASK_BECOME_PASS_OPT,
    become_password: str | None = BECOME_PASSWORD_OPT,
) -> None:
    deps = build_deps(
        _require_seam(ctx),
        become_password=_resolve_become_password(ask_become_pass, become_password),
    )
    renderer: Renderer = ctx.obj["renderer"]
    _render_run(renderer, lambda: deps.bootstrap.bootstrap(check=check), "bootstrap")


@app.command(help="Resolve every manifest in --manifests-dir (read-only seam check)")
def manifests(ctx: typer.Context) -> None:
    """Read every ``*.yaml`` manifest from the composition manifests dir.

    This is the seam's self-check: it proves the engine can resolve the
    composition's manifests without a composition checkout inside the engine
    tree. It reads only the manifests — no playbook runs, nothing is written.
    """
    settings = _require_seam(ctx)
    renderer: Renderer = ctx.obj["renderer"]
    manifest_paths = sorted(settings.seam.manifests_dir.glob("*.yaml"))
    if not manifest_paths:
        renderer.error(
            ErrorView(
                kind="NoManifestsFound",
                message=(
                    f"no *.yaml manifests under {settings.seam.manifests_dir} — "
                    f"--manifests-dir must point at the composition's "
                    f"dotfiles/provisioning/"
                ),
            )
        )
        raise typer.Exit(code=1) from None
    reader = YamlManifestReader()
    resolved: dict[str, str] = {}
    try:
        for path in manifest_paths:
            manifest = reader.read(path)
            resolved[path.name] = manifest.kind.value
    except ManifestReadError as exc:
        renderer.error(ErrorView(kind="ManifestReadError", message=str(exc)))
        raise typer.Exit(code=1) from None
    renderer.result(
        ResultView(
            success=True,
            title="manifests",
            fields={
                "manifests_dir": str(settings.seam.manifests_dir),
                "composition_root": str(settings.seam.composition_root),
                "count": len(resolved),
                "manifests": resolved,
            },
        )
    )


@app.command(help="Show the installed package version")
def version(ctx: typer.Context) -> None:
    try:
        ver = _pkg_version("dotfiles-provision")
    except PackageNotFoundError:
        ctx.obj["renderer"].error(
            ErrorView(
                kind="PackageNotFoundError",
                message="dotfiles-provision package not installed",
            )
        )
        raise typer.Exit(code=1) from None

    ctx.obj["renderer"].custom(CustomView(plain=ver, object={"version": ver}, rich=ver))


if __name__ == "__main__":
    app()
