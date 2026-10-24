# Design — package group_vars next to the inventory

## D1. Canonical location is `ansible/inventory/group_vars/`

Ansible loads `group_vars` next to the inventory file. The source previously
kept the files at `ansible/group_vars/` and relied on a symlink from
`ansible/inventory/group_vars`. Hatchling's sdist follows the symlink for the
source layout but does not materialize the inventory-side directory, so the
installed wheel loses it. Making `ansible/inventory/group_vars/` the real
directory removes the packaging edge entirely.

## D2. No duplicate group_vars tree

The old `ansible/group_vars` path is removed rather than copied. Tests read the
canonical `inventory/group_vars` path; the inventory-based Ansible runs (the CLI
always passes `-i`) resolve the same files. The archive/history references to
the old path are historical.

## D3. `make build` proves the wheel layout

`scripts/check-wheel-contents.py` opens the newest wheel and asserts the Ansible
config, inventory and three group_vars files are inside
`provisioning/_ansible/`. `make build` runs it after `uv build`; the release CI
job therefore cannot ship a wheel without them. The check uses only the stdlib.

## Verification plan

| Claim | Command | Expected |
| --- | --- | --- |
| Source layout | `test -f ansible/inventory/group_vars/all.yml` | exit 0 |
| Wheel layout | `make build` | `PASS: ... carries the Ansible tree + inventory/group_vars` |
| Source tests | `uv run pytest -q tests/unit/test_ansible_scaffold.py` | exit 0 |
| Installed engine verify | `make provision ARGS="verify --expected-engine-tag v0.1.9"` | exit 0 after the composition pin bump |
