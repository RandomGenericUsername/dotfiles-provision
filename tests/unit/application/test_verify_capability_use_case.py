from __future__ import annotations

from pathlib import Path

import pytest

from provisioning.application import CompositionSeam, VerifyCapabilityUseCase
from provisioning.domain.models import ProvisionResult
from tests.unit.application.conftest import FakeExecutor, FakeFactReader, RaisingExecutor

_SEAM = CompositionSeam(Path("/composition/dotfiles/provisioning"), Path("/composition"))


class TestVerifyCapabilityUseCase:
    def test_verify_runs_executor_with_check_false(self) -> None:
        executor = FakeExecutor(ProvisionResult(success=True))
        use_case = VerifyCapabilityUseCase(
            executor=executor,
            fact_reader=FakeFactReader("arch"),
            playbook=Path("verify.yaml"),
            seam=_SEAM,
        )
        use_case.verify()
        assert len(executor.calls) == 1
        assert executor.calls[0][1] is False

    def test_default_playbook_is_verify_yaml(self) -> None:
        executor = FakeExecutor(ProvisionResult(success=True))
        use_case = VerifyCapabilityUseCase(
            executor=executor,
            fact_reader=FakeFactReader("arch"),
        )
        use_case.verify()
        assert len(executor.calls) == 1
        assert executor.calls[0][0] == Path("verify.yaml")

    def test_injected_playbook_is_passed_through(self) -> None:
        executor = FakeExecutor(ProvisionResult(success=True))
        use_case = VerifyCapabilityUseCase(
            executor=executor,
            fact_reader=FakeFactReader("arch"),
            playbook=Path("playbooks/verify.yaml"),
            seam=_SEAM,
        )
        use_case.verify()
        assert len(executor.calls) == 1
        assert executor.calls[0][0] == Path("playbooks/verify.yaml")

    def test_extra_vars_carry_exactly_install_dir_and_os_family(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("XDG_DATA_HOME", "/home/user/.local/share")
        executor = FakeExecutor(ProvisionResult(success=True))
        use_case = VerifyCapabilityUseCase(
            executor=executor,
            fact_reader=FakeFactReader("debian-family"),
            playbook=Path("verify.yaml"),
            seam=_SEAM,
        )
        use_case.verify()
        assert len(executor.calls) == 1
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

    def test_expected_engine_tag_is_forwarded_as_an_extra_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """R-17: the composition pin reaches the role as `expected_engine_tag`.

        It is a fifth key only when requested, so the four-key seam contract is
        unchanged for a default verify.
        """
        monkeypatch.setenv("XDG_DATA_HOME", "/home/user/.local/share")
        executor = FakeExecutor(ProvisionResult(success=True))
        use_case = VerifyCapabilityUseCase(
            executor=executor,
            fact_reader=FakeFactReader("debian-family"),
            playbook=Path("verify.yaml"),
            seam=_SEAM,
        )
        use_case.verify(expected_engine_tag="v9.9.9")
        extra_vars = executor.calls[0][2]
        assert extra_vars["expected_engine_tag"] == "v9.9.9"
        assert set(extra_vars) == {
            "install_dir",
            "os_family",
            "manifests_dir",
            "composition_root",
            "expected_engine_tag",
        }

    def test_blank_expected_engine_tag_is_not_forwarded(self) -> None:
        executor = FakeExecutor(ProvisionResult(success=True))
        use_case = VerifyCapabilityUseCase(
            executor=executor,
            fact_reader=FakeFactReader("arch"),
            playbook=Path("verify.yaml"),
            seam=_SEAM,
        )
        use_case.verify(expected_engine_tag="   ")
        assert "expected_engine_tag" not in executor.calls[0][2]

    def test_result_returned_unchanged(self) -> None:
        expected = ProvisionResult(
            success=False,
            tasks=(("verify : assert preconditions", "failed"),),
            returncode=3,
            stderr="fatal: [localhost]: FAILED!",
        )
        executor = FakeExecutor(expected)
        use_case = VerifyCapabilityUseCase(
            executor=executor,
            fact_reader=FakeFactReader("arch"),
            playbook=Path("verify.yaml"),
            seam=_SEAM,
        )
        result = use_case.verify()
        assert len(executor.calls) == 1
        assert result == expected

    def test_executor_errors_propagate(self) -> None:
        use_case = VerifyCapabilityUseCase(
            executor=RaisingExecutor(),
            fact_reader=FakeFactReader("arch"),
            playbook=Path("verify.yaml"),
            seam=_SEAM,
        )
        with pytest.raises(RuntimeError, match="boom"):
            use_case.verify()
