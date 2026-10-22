"""R-15 packaging contract: the wheel carries the Ansible tree the CLI runs.

The wheel is the installable engine (``uv tool install git+…@tag``), so the
tree must be package data and the resolver must prefer it. These tests are
static/unit-fast: the executed wheel proof lives in the release procedure
(``uv build`` + ``unzip -l`` + isolated ``uv tool install``).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from provisioning.cli import main as cli_main

ROOT = Path(__file__).resolve().parents[1]


def test_wheel_force_includes_the_ansible_tree() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    wheel = data["tool"]["hatch"]["build"]["targets"]["wheel"]
    assert wheel["force-include"]["ansible"] == "provisioning/_ansible", (
        "the wheel must package ansible/ inside the Python package; a wheel "
        "without it cannot run a playbook from a tool install"
    )


def test_resolver_prefers_the_packaged_tree(
    monkeypatch, tmp_path: Path
) -> None:
    packaged = tmp_path / "_ansible"
    packaged.mkdir()
    monkeypatch.setattr(cli_main, "_resource_files", lambda package: tmp_path)
    assert cli_main._resolve_ansible_root() == packaged


def test_checkout_resolution_finds_the_engine_inputs() -> None:
    """The editable/source fallback resolves the real inventory + playbooks."""
    assert (cli_main._ANSIBLE_ROOT / "inventory" / "localhost.yaml").is_file()
    assert (cli_main._ANSIBLE_ROOT / "playbooks" / "verify.yaml").is_file()
    assert (cli_main._ANSIBLE_ROOT / "ansible.cfg").is_file()


def test_default_inventory_lives_under_the_resolved_root() -> None:
    assert cli_main.default_inventory() == (
        cli_main._ANSIBLE_ROOT / "inventory" / "localhost.yaml"
    )
