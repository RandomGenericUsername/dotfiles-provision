"""Regression tests for the structural pin audit (`scripts/pin-audit.py`).

The audit is intentionally narrower than `verify`: it must fail fast on pin or
skin-inventory drift before a pin-only release runs the full gates. These tests
use a minimal temp repo root so a missing/extra skin manifest or consumer target
can be proven without touching the checkout.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_ENGINE_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ENGINE_ROOT / "scripts" / "pin-audit.py"


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
        timeout=60,
    )


def _minimal_root(tmp_path: Path) -> Path:
    """Copy only the inputs the structural audit reads."""
    root = tmp_path / "repo"
    fixtures = (
        "tests/fixtures/composition/dotfiles/provisioning/assets.yaml",
        "tests/fixtures/composition/dotfiles/provisioning/program-tuple.yaml",
        "tests/fixtures/composition/dotfiles/provisioning/apps.yaml",
        "tests/fixtures/ags-apps/app-list/all-standalone.apps.yaml",
        "ansible/roles/verify/vars/main.yml",
    )
    for relative in fixtures:
        source = _ENGINE_ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return root


def _edit_verify_list(root: Path, key: str, mutate) -> None:
    path = root / "ansible/roles/verify/vars/main.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    mutate(data[key])
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_repository_pin_audit_passes() -> None:
    result = _run(_ENGINE_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "pin-audit: PASS" in result.stdout
    assert "skins=5" in result.stdout
    assert "targets=10" in result.stdout
    assert "artifacts=2" in result.stdout


def test_missing_terminal_host_manifest_fails(tmp_path: Path) -> None:
    root = _minimal_root(tmp_path)
    _edit_verify_list(
        root,
        "verify_skins_manifest_names",
        lambda names: names.remove("terminal-host"),
    )
    result = _run(root)
    assert result.returncode == 1
    assert "verify_skins_manifest_names" in result.stderr
    assert "terminal-host" in result.stderr


def test_extra_skin_manifest_fails(tmp_path: Path) -> None:
    root = _minimal_root(tmp_path)
    _edit_verify_list(
        root,
        "verify_skins_manifest_names",
        lambda names: names.append("legacy"),
    )
    result = _run(root)
    assert result.returncode == 1
    assert "verify_skins_manifest_names" in result.stderr


def test_missing_wlogout_consumer_target_fails(tmp_path: Path) -> None:
    root = _minimal_root(tmp_path)
    _edit_verify_list(
        root,
        "verify_skins_template_files",
        lambda files: files.remove("wlogout.gtk.css.j2"),
    )
    result = _run(root)
    assert result.returncode == 1
    assert "verify_skins_template_files" in result.stderr
    assert "wlogout.gtk.css.j2" in result.stderr


def test_missing_gtk_consumer_target_fails(tmp_path: Path) -> None:
    root = _minimal_root(tmp_path)
    _edit_verify_list(
        root,
        "verify_skins_template_files",
        lambda files: files.remove("gtk3.gtk.css.j2"),
    )
    result = _run(root)
    assert result.returncode == 1
    assert "verify_skins_template_files" in result.stderr
    assert "gtk3.gtk.css.j2" in result.stderr


@pytest.mark.parametrize("artifact", ["rofi.rasi.j2", "kitty.conf.j2"])
def test_missing_skin_artifact_fails(tmp_path: Path, artifact: str) -> None:
    root = _minimal_root(tmp_path)
    _edit_verify_list(
        root,
        "verify_skins_artifact_files",
        lambda files: files.remove(artifact),
    )
    result = _run(root)
    assert result.returncode == 1
    assert "verify_skins_artifact_files" in result.stderr
    assert artifact in result.stderr


def test_extra_skin_target_fails(tmp_path: Path) -> None:
    root = _minimal_root(tmp_path)
    _edit_verify_list(
        root,
        "verify_skins_template_files",
        lambda files: files.append("ags-retired.gtk.css.j2"),
    )
    result = _run(root)
    assert result.returncode == 1
    assert "verify_skins_template_files" in result.stderr


def test_extra_skin_artifact_fails(tmp_path: Path) -> None:
    root = _minimal_root(tmp_path)
    _edit_verify_list(
        root,
        "verify_skins_artifact_files",
        lambda files: files.append("btop.conf.j2"),
    )
    result = _run(root)
    assert result.returncode == 1
    assert "verify_skins_artifact_files" in result.stderr
