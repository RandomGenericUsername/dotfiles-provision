# repo-harness (delta)

## ADDED Requirements

### Requirement: the wheel carries the Ansible inventory and group_vars

The built wheel SHALL contain `provisioning/_ansible/ansible.cfg`,
`provisioning/_ansible/inventory/localhost.yaml` and
`provisioning/_ansible/inventory/group_vars/{all,arch,debian-family}.yml`. The
canonical group_vars SHALL live in the real `ansible/inventory/group_vars/`
directory. `make build` SHALL fail if any required path is missing from the
wheel.

Source: BUG-002; `ansible.cfg` inventory discovery; `scripts/check-wheel-contents.py`.

#### Scenario: the wheel layout is checked

- **WHEN** `make build` runs
- **THEN** `uv build` produces the wheel and the content check prints
  `PASS: ... carries the Ansible tree + inventory/group_vars`

#### Scenario: the installed engine resolves group_vars

- **WHEN** the installed engine runs `verify` with its packaged inventory
- **THEN** `container_runtime_engine` and the `shell` vars are defined, because
  `inventory/group_vars/*.yml` sits next to `localhost.yaml`
