"""AD-17 composition seam — the engine learns composition paths ONLY from flags.

The engine repo owns the Ansible tree but **not** the composition checkout. A
fresh engine clone has no ``dotfiles/provisioning/`` above it, so no role may
derive a composition path from ``{{ playbook_dir }}``. The CLI resolves the
seam once (``--manifests-dir`` / ``--composition-root``) and passes it to
Ansible as extra-vars.

These tests are the executable form of that contract:

- an external ``--manifests-dir`` resolves every manifest, from a cwd that has
  no composition tree of its own;
- a missing or wrong path fails loud as a usage error, not deep in Ansible;
- no role var, task, playbook or template derives a path from ``playbook_dir``;
- the executor receives exactly the four seam keys.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner, Result

from provisioning.application import CompositionPathError, CompositionSeam
from provisioning.application.use_cases import _seam_extra_vars
from provisioning.cli.main import app
from tests.support import ENGINE_ROOT, FIXTURE_COMPOSITION, manifests_dir
from tests.unit.application.conftest import FakeFactReader

runner = CliRunner()

#: Every manifest the composition currently ships, by kind. The seam check
#: resolves each one through the real reader, so a new manifest must be added
#: here (and to the fixture) deliberately.
_EXPECTED_MANIFEST_KINDS = {
    "assets.yaml": "assets",
    "cli-tools.yaml": "cli-tools",
    "config-copies.yaml": "config-copies",
    "filesystem.yaml": "filesystem",
    "packages.yaml": "packages",
}


def _invoke(args: list[str], cwd: Path, monkeypatch: pytest.MonkeyPatch) -> Result:
    """Run the real CLI from ``cwd`` (the callback resolves against it)."""
    monkeypatch.chdir(cwd)
    return runner.invoke(app, args)


class TestExternalManifestsDir:
    def test_resolves_every_manifest_from_a_foreign_cwd(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The load-bearing seam: run from the ENGINE root (no ``dotfiles/``
        child) with an external ``--manifests-dir``; every manifest resolves.

        This is the exact shape of a deployed engine reading a composition
        checkout somewhere else on disk.
        """
        external = manifests_dir()
        assert not (ENGINE_ROOT / "dotfiles" / "provisioning").exists(), (
            "this test is only meaningful when the engine checkout has no "
            "composition child; if that changes, the default seam proves nothing"
        )
        result = _invoke(
            [
                "--output-format",
                "json",
                "--manifests-dir",
                str(external),
                "manifests",
            ],
            ENGINE_ROOT,
            monkeypatch,
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["success"] is True
        assert payload["manifests_dir"] == str(external)
        assert payload["composition_root"] == str(external.parent.parent)
        assert payload["count"] == len(_EXPECTED_MANIFEST_KINDS)
        assert payload["manifests"] == _EXPECTED_MANIFEST_KINDS
        # Composition DATA records (AD-31/34) live beside the manifests but are
        # not `kind:` manifests; the seam check must skip them deliberately.
        assert "apps.yaml" not in payload["manifests"]
        assert "program-tuple.yaml" not in payload["manifests"]

    def test_external_dir_wins_over_the_cwd_default(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An explicit flag is authoritative even when a composition IS under
        the cwd: the engine must never silently prefer the nearer tree."""
        decoy = tmp_path / "dotfiles" / "provisioning"
        decoy.mkdir(parents=True)
        (decoy / "decoy.yaml").write_text("kind: packages\npackages: []\n")
        result = _invoke(
            [
                "--output-format",
                "json",
                "--manifests-dir",
                str(manifests_dir()),
                "manifests",
            ],
            tmp_path,
            monkeypatch,
        )
        assert result.exit_code == 0, result.stderr
        payload = json.loads(result.stdout)
        assert "decoy.yaml" not in payload["manifests"]
        assert payload["manifests"] == _EXPECTED_MANIFEST_KINDS

    def test_missing_manifests_dir_fails_loud(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        result = _invoke(
            [
                "--output-format",
                "json",
                "--manifests-dir",
                str(tmp_path / "nope"),
                "manifests",
            ],
            ENGINE_ROOT,
            monkeypatch,
        )
        assert result.exit_code == 2
        payload = json.loads(result.stdout + result.stderr)
        assert payload["kind"] == "CompositionPathError"
        assert "--manifests-dir" in payload["message"]

    def test_manifests_dir_without_a_composition_root_fails_loud(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """The manifests can live elsewhere, but ``composition_root`` must
        still be the checkout that owns ``dotfiles/provisioning/`` (it is where
        ``config/btop/`` is read from)."""
        stray = tmp_path / "manifests"
        stray.mkdir()
        (stray / "packages.yaml").write_text("kind: packages\npackages: []\n")
        result = _invoke(
            [
                "--output-format",
                "json",
                "--manifests-dir",
                str(stray),
                "manifests",
            ],
            ENGINE_ROOT,
            monkeypatch,
        )
        assert result.exit_code == 2
        payload = json.loads(result.stdout + result.stderr)
        assert payload["kind"] == "CompositionPathError"
        assert "dotfiles/provisioning/" in payload["message"]


class TestSeamResolution:
    def test_explicit_paths_are_resolved_once(self) -> None:
        seam = CompositionSeam.resolve(
            manifests_dir=manifests_dir(), composition_root=FIXTURE_COMPOSITION
        )
        assert seam.manifests_dir == manifests_dir()
        assert seam.composition_root == FIXTURE_COMPOSITION

    def test_documented_default_layout(self) -> None:
        """``--manifests-dir`` defaults to ``<cwd>/dotfiles/provisioning`` and
        ``--composition-root`` to its grandparent."""
        seam = CompositionSeam.resolve(cwd=FIXTURE_COMPOSITION)
        assert seam.manifests_dir == FIXTURE_COMPOSITION / "dotfiles" / "provisioning"
        assert seam.composition_root == FIXTURE_COMPOSITION

    def test_validate_returns_self_for_a_real_composition(self) -> None:
        seam = CompositionSeam.resolve(
            manifests_dir=manifests_dir(), composition_root=FIXTURE_COMPOSITION
        )
        assert seam.validate() is seam

    def test_validate_names_the_bad_path(self, tmp_path: Path) -> None:
        seam = CompositionSeam(manifests_dir=tmp_path / "missing", composition_root=tmp_path)
        with pytest.raises(CompositionPathError, match="--manifests-dir"):
            seam.validate()


class TestExtraVars:
    def test_seam_extra_vars_are_exactly_the_four_keys(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("XDG_DATA_HOME", "/home/user/.local/share")
        seam = CompositionSeam.resolve(
            manifests_dir=manifests_dir(), composition_root=FIXTURE_COMPOSITION
        )
        extra_vars = _seam_extra_vars(FakeFactReader("arch"), seam)
        assert extra_vars == {
            "install_dir": "/home/user/.local/share/dotfiles",
            "os_family": "arch",
            "manifests_dir": str(manifests_dir()),
            "composition_root": str(FIXTURE_COMPOSITION),
        }


class TestNoRoleDerivesFromPlaybookDir:
    """AD-17 static guard: the derivation must not come back.

    Scans the whole Ansible tree — vars/tasks/defaults/handlers/playbooks
    (parsed YAML, comments excluded) AND templates (raw Jinja expressions) —
    for a ``playbook_dir`` reference or a ``../../../..`` climb. Both would
    resolve inside an engine checkout that ships no composition.
    """

    _ANSIBLE = ENGINE_ROOT / "ansible"
    _JINJA_PLAYBOOK_DIR = re.compile(r"\{[{%][^}]*\bplaybook_dir\b")
    _REPO_CLIMB = re.compile(r"(?:\.\./){4,}")

    def _yaml_files(self) -> list[Path]:
        return sorted(
            path
            for path in self._ANSIBLE.rglob("*")
            if path.suffix in {".yml", ".yaml"} and path.is_file()
        )

    def _template_files(self) -> list[Path]:
        return sorted(self._ANSIBLE.rglob("*.j2"))

    def test_yaml_values_never_reference_playbook_dir(self) -> None:
        offenders: list[str] = []
        for path in self._yaml_files():
            document = yaml.safe_load(path.read_text())
            if self._contains_playbook_dir(document):
                offenders.append(str(path.relative_to(ENGINE_ROOT)))
        assert offenders == [], (
            "no role/task/playbook may derive a path from playbook_dir (AD-17): "
            + ", ".join(offenders)
        )

    def test_templates_never_reference_playbook_dir(self) -> None:
        offenders = [
            str(path.relative_to(ENGINE_ROOT))
            for path in self._template_files()
            if self._JINJA_PLAYBOOK_DIR.search(path.read_text())
        ]
        assert offenders == []

    def test_no_four_level_repo_climb_anywhere_in_ansible(self) -> None:
        offenders = [
            str(path.relative_to(ENGINE_ROOT))
            for path in [*self._yaml_files(), *self._template_files()]
            if self._REPO_CLIMB.search(path.read_text())
        ]
        assert offenders == [], (
            "a ../../../../ climb from the playbook resolves to the ENGINE "
            "checkout, not a composition; pass manifests_dir/composition_root: "
            + ", ".join(offenders)
        )

    @classmethod
    def _contains_playbook_dir(cls, value: object) -> bool:
        if isinstance(value, str):
            return "playbook_dir" in value
        if isinstance(value, dict):
            return any(
                cls._contains_playbook_dir(key) or cls._contains_playbook_dir(item)
                for key, item in value.items()
            )
        if isinstance(value, list):
            return any(cls._contains_playbook_dir(item) for item in value)
        return False
