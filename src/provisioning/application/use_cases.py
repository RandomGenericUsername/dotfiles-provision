"""Use cases for the provisioning orchestrator.

The application layer wires the locked ports (Story 1.4) into three use
cases that run playbooks through ``IProvisionExecutor``:

- ``ProvisionMachineUseCase`` plans (``check=True``) or applies
  (``check=False``) machine state.
- ``VerifyCapabilityUseCase`` asserts the §12 runtime preconditions via the
  verify playbook (always a real check, never ``--check``).
- ``BootstrapUseCase`` runs the aggregate bootstrap playbook end-to-end
  (``check=True`` supports ``bootstrap --check``).

All three resolve the seam extra-vars — ``install_dir``, ``os_family``,
``manifests_dir`` and ``composition_root`` — via the shared
``_seam_extra_vars`` helper and hand them to the executor.

The composition seam (AD-17) is resolved ONCE here, from CLI input, and then
passed down to Ansible. No role derives a composition path from
``playbook_dir``: this repository is the pinned engine and a fresh engine
checkout has no composition ancestors.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from provisioning.domain.models import ProvisionResult
from provisioning.ports import IFactReader, IProvisionExecutor


class CompositionPathError(ValueError):
    """Raised when the composition seam points at nothing."""


def resolve_install_dir() -> Path:
    """Resolve the install spine root: ``$XDG_DATA_HOME/dotfiles/``.

    Defaults to ``~/.local/share/dotfiles/`` when ``XDG_DATA_HOME`` is unset
    (SPEC / chaining-spine contract). The result is an absolute path.
    """
    data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(data_home) if data_home else Path.home() / ".local" / "share"
    return (base / "dotfiles").expanduser().resolve()


@dataclass(frozen=True)
class CompositionSeam:
    """The two composition-repo paths the engine is allowed to read.

    ``manifests_dir`` is the composition's ``dotfiles/provisioning/`` (the
    manifest set the engine validates and the ``scripts/`` it deploys);
    ``composition_root`` is the checkout root (``dotfiles/`` and
    ``src/runtime/`` live under it). Both are absolute and resolved once.

    The defaults document the composition layout rather than assuming a
    sibling checkout: ``--manifests-dir`` defaults to
    ``<cwd>/dotfiles/provisioning`` and ``--composition-root`` to that
    directory's grandparent. An explicit flag always wins.
    """

    manifests_dir: Path
    composition_root: Path

    @classmethod
    def resolve(
        cls,
        manifests_dir: Path | None = None,
        composition_root: Path | None = None,
        cwd: Path | None = None,
    ) -> CompositionSeam:
        base = (cwd or Path.cwd()).expanduser().resolve()
        resolved_manifests = (
            manifests_dir.expanduser().resolve()
            if manifests_dir is not None
            else (base / "dotfiles" / "provisioning").resolve()
        )
        resolved_root = (
            composition_root.expanduser().resolve()
            if composition_root is not None
            else resolved_manifests.parent.parent
        )
        return cls(manifests_dir=resolved_manifests, composition_root=resolved_root)

    def validate(self) -> CompositionSeam:
        """Return self when both paths exist; raise ``CompositionPathError``.

        Called by the CLI before any playbook starts, so a typo fails at the
        seam instead of deep inside an Ansible task with an empty path.
        """
        if not self.manifests_dir.is_dir():
            raise CompositionPathError(
                f"--manifests-dir is not a directory: {self.manifests_dir}. It must "
                f"point at the composition repo's dotfiles/provisioning/ (pass "
                f"--manifests-dir explicitly when running outside a composition "
                f"checkout)."
            )
        if not self.composition_root.is_dir():
            raise CompositionPathError(
                f"--composition-root is not a directory: {self.composition_root}. It "
                f"must point at the composition repo checkout (the parent of "
                f"dotfiles/provisioning/); pass --composition-root explicitly when "
                f"the manifests live elsewhere."
            )
        if not (self.composition_root / "dotfiles" / "provisioning").is_dir():
            raise CompositionPathError(
                f"--composition-root {self.composition_root} does not contain "
                f"dotfiles/provisioning/. The engine reads composition-owned files "
                f"(provisioning/scripts/, config/btop/, src/runtime/) from this root."
            )
        return self


def _seam_extra_vars(fact_reader: IFactReader, seam: CompositionSeam) -> dict[str, str]:
    """Resolve the four locked seam extra-vars for a provisioning run.

    Returns exactly ``install_dir`` (resolved spine root), ``os_family`` (the
    ``group_vars`` basename), ``manifests_dir`` and ``composition_root`` — the
    keys the seam contract test pins and no others.
    """
    return {
        "install_dir": str(resolve_install_dir()),
        "os_family": fact_reader.os_family(),
        "manifests_dir": str(seam.manifests_dir),
        "composition_root": str(seam.composition_root),
    }


class ProvisionMachineUseCase:
    """Plan or apply machine state through the locked provisioning ports.

    ``check=True`` is plan mode (no system changes); ``check=False`` is apply
    mode. The ``os_family`` seam is read from ``IFactReader``, the install dir
    is resolved here, and the composition seam is supplied by the CLI — all
    four are passed via the ``extra_vars`` seam.
    """

    def __init__(
        self,
        executor: IProvisionExecutor,
        fact_reader: IFactReader,
        playbook: Path = Path("bootstrap.yaml"),
        seam: CompositionSeam | None = None,
    ) -> None:
        self._executor = executor
        self._fact_reader = fact_reader
        self._playbook = playbook
        self._seam = seam or CompositionSeam.resolve()

    def provision(self, check: bool) -> ProvisionResult:
        return self._executor.run(
            self._playbook, check, _seam_extra_vars(self._fact_reader, self._seam)
        )


class VerifyCapabilityUseCase:
    """Assert the §12 runtime preconditions via the verify playbook.

    The four preconditions (binaries installed, assets placed, filesystem
    structure exists, settings files parseable) are asserted by the Ansible
    ``verify.yaml`` playbook (Epic 2 content) — this use case is the Python
    orchestration seam that runs it through ``IProvisionExecutor`` with a real
    check (never ``--check``), without reaching into provisioning internals.
    ``verify`` reads the deployed spine, so the composition seam is passed for
    symmetry and for the manifest-resolution report; it writes nothing under
    the composition checkout.
    """

    def __init__(
        self,
        executor: IProvisionExecutor,
        fact_reader: IFactReader,
        playbook: Path = Path("verify.yaml"),
        seam: CompositionSeam | None = None,
    ) -> None:
        self._executor = executor
        self._fact_reader = fact_reader
        self._playbook = playbook
        self._seam = seam or CompositionSeam.resolve()

    def verify(self) -> ProvisionResult:
        return self._executor.run(
            self._playbook, False, _seam_extra_vars(self._fact_reader, self._seam)
        )


class BootstrapUseCase:
    """Run the aggregate ``bootstrap.yaml`` playbook end-to-end.

    ``check=True`` supports ``dotfiles-provision bootstrap --check``; the
    default ``check=False`` is the full end-to-end provisioning run (FR-4).
    """

    def __init__(
        self,
        executor: IProvisionExecutor,
        fact_reader: IFactReader,
        playbook: Path = Path("bootstrap.yaml"),
        seam: CompositionSeam | None = None,
    ) -> None:
        self._executor = executor
        self._fact_reader = fact_reader
        self._playbook = playbook
        self._seam = seam or CompositionSeam.resolve()

    def bootstrap(self, check: bool = False) -> ProvisionResult:
        return self._executor.run(
            self._playbook, check, _seam_extra_vars(self._fact_reader, self._seam)
        )


__all__ = [
    "BootstrapUseCase",
    "CompositionPathError",
    "CompositionSeam",
    "ProvisionMachineUseCase",
    "VerifyCapabilityUseCase",
    "resolve_install_dir",
]
