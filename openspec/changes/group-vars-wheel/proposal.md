# group-vars-wheel

## Why

`dotfiles-provision@v0.1.8` installs a wheel whose
`provisioning/_ansible/inventory/` has only `localhost.yaml`. The source
`ansible/inventory/group_vars` was a symlink to `../group_vars`; the sdist/wheel
build dropped it. Ansible therefore loads no `all.yml`/`arch.yml`/
`debian-family.yml` for the installed engine, and `make provision` fails with
`container_runtime_engine` undefined (then `shell`). `bootstrap.sh` hides the
bug because it passes the cached checkout's inventory.

Evidence: the installed
`~/.local/share/uv/tools/dotfiles-provision/.../provisioning/_ansible/inventory/`
contains only `localhost.yaml`; `verify` fails at the weg image task.
Verify: `ls .../_ansible/inventory`.

## What Changes

- Move the canonical group_vars to the real `ansible/inventory/group_vars/`
  directory (the convention Ansible discovers next to the inventory).
- Remove the fragile `ansible/group_vars` symlink; update source tests to read
  the inventory path.
- Add `scripts/check-wheel-contents.py`; `make build` runs it and fails if the
  wheel lacks `ansible.cfg`, the inventory, or the three group_vars files.
- Release `v0.1.9`.

## Capabilities

- **Modified Capabilities:** `repo-harness` — a wheel-layout requirement.

## Non-goals

- No change to runtime, roles, playbooks or the composition.
- No change to the group_vars values.

## Impact

- Moved: `ansible/group_vars/*.yml` → `ansible/inventory/group_vars/*.yml`.
- Removed: the `ansible/group_vars` symlink.
- Modified: `ansible/ansible.cfg` comment, `tests/unit/test_ansible_scaffold.py`,
  `Makefile` (`build` check), `pyproject.toml` version, `CHANGELOG.md`, ticket,
  OpenSpec change.
