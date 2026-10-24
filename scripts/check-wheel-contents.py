#!/usr/bin/env python3
"""Assert the built wheel carries the engine's Ansible inventory and group_vars.

BUG-002: the wheel force-includes `ansible/` as `provisioning/_ansible`, but a
symlinked `inventory/group_vars` was silently dropped. The installed engine then
ran `verify` without `container_runtime_engine` / `shell`, because Ansible only
finds group_vars next to the inventory (or playbook). The canonical files now
live in the real `ansible/inventory/group_vars/` directory, and this check makes
`make build` fail if the wheel loses them again.

Usage: python3 scripts/check-wheel-contents.py [--dist DIST]
Exit 0 = every required path is inside the newest built wheel.
Exit 1 = no wheel, or a required path is missing.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

REQUIRED = (
    "provisioning/_ansible/ansible.cfg",
    "provisioning/_ansible/inventory/localhost.yaml",
    "provisioning/_ansible/inventory/group_vars/all.yml",
    "provisioning/_ansible/inventory/group_vars/arch.yml",
    "provisioning/_ansible/inventory/group_vars/debian-family.yml",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dist",
        default=str(Path(__file__).resolve().parents[1] / "dist"),
        help="directory containing the built wheel",
    )
    args = parser.parse_args()
    dist = Path(args.dist)
    wheels = sorted(dist.glob("dotfiles_provision-*.whl"))
    if not wheels:
        print(f"FAIL: no dotfiles_provision wheel under {dist}", file=sys.stderr)
        return 1
    wheel = wheels[-1]
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    missing = [name for name in REQUIRED if name not in names]
    if missing:
        print(
            f"FAIL: {wheel.name} is missing the packaged Ansible paths: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        return 1
    print(f"PASS: {wheel.name} carries the Ansible tree + inventory/group_vars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
