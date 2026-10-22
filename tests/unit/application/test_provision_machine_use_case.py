from __future__ import annotations

from pathlib import Path

import pytest

from provisioning.application import CompositionSeam, ProvisionMachineUseCase
from provisioning.application.use_cases import resolve_install_dir
from provisioning.domain.models import ProvisionResult
from tests.unit.application.conftest import FakeExecutor, FakeFactReader

_SEAM = CompositionSeam(Path("/composition/dotfiles/provisioning"), Path("/composition"))


class TestProvisionMachineUseCase:
    def test_check_true_is_plan_mode(self) -> None:
        executor = FakeExecutor(ProvisionResult(success=True))
        use_case = ProvisionMachineUseCase(
            executor=executor,
            fact_reader=FakeFactReader("arch"),
            playbook=Path("bootstrap.yaml"),
            seam=_SEAM,
        )
        use_case.provision(check=True)
        assert executor.calls[0][1] is True

    def test_check_false_is_apply_mode(self) -> None:
        executor = FakeExecutor(ProvisionResult(success=True))
        use_case = ProvisionMachineUseCase(
            executor=executor,
            fact_reader=FakeFactReader("arch"),
            playbook=Path("bootstrap.yaml"),
            seam=_SEAM,
        )
        use_case.provision(check=False)
        assert executor.calls[0][1] is False

    def test_playbook_is_passed_through(self) -> None:
        executor = FakeExecutor(ProvisionResult(success=True))
        use_case = ProvisionMachineUseCase(
            executor=executor,
            fact_reader=FakeFactReader("arch"),
            playbook=Path("playbooks/bootstrap.yaml"),
            seam=_SEAM,
        )
        use_case.provision(check=True)
        assert executor.calls[0][0] == Path("playbooks/bootstrap.yaml")

    def test_extra_vars_carry_the_four_seam_keys(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("XDG_DATA_HOME", "/home/user/.local/share")
        executor = FakeExecutor(ProvisionResult(success=True))
        use_case = ProvisionMachineUseCase(
            executor=executor,
            fact_reader=FakeFactReader("debian-family"),
            playbook=Path("bootstrap.yaml"),
            seam=_SEAM,
        )
        use_case.provision(check=True)
        extra_vars = executor.calls[0][2]
        assert extra_vars == {
            "install_dir": str(Path("/home/user/.local/share/dotfiles")),
            "os_family": "debian-family",
            "manifests_dir": "/composition/dotfiles/provisioning",
            "composition_root": "/composition",
        }
        assert set(extra_vars) == {
            "install_dir",
            "os_family",
            "manifests_dir",
            "composition_root",
        }

    def test_result_returned_unchanged(self) -> None:
        expected = ProvisionResult(success=False, tasks=(("packages : TASK", "failed"),))
        executor = FakeExecutor(expected)
        use_case = ProvisionMachineUseCase(
            executor=executor,
            fact_reader=FakeFactReader("arch"),
            playbook=Path("bootstrap.yaml"),
            seam=_SEAM,
        )
        result = use_case.provision(check=False)
        assert result == expected


class TestResolveInstallDir:
    def test_uses_xdg_data_home_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")
        assert resolve_install_dir() == Path("/custom/data/dotfiles")
        assert resolve_install_dir().is_absolute()

    def test_relative_xdg_data_home_is_normalized_absolute(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("XDG_DATA_HOME", "data/share")
        resolved = resolve_install_dir()
        assert resolved == Path("data/share/dotfiles").resolve()
        assert resolved.is_absolute()

    def test_tilde_xdg_data_home_is_expanded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("XDG_DATA_HOME", "~/data")
        resolved = resolve_install_dir()
        assert resolved == Path("~/data/dotfiles").expanduser().resolve()
        assert resolved.is_absolute()

    def test_defaults_to_local_share_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: Path("/home/fake")))
        assert resolve_install_dir() == Path("/home/fake/.local/share/dotfiles")
        assert resolve_install_dir().is_absolute()
