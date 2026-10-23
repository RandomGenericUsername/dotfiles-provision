# runtime-consumption (delta)

## ADDED Requirements

### Requirement: the seed step runs the installed pinned runtime

`ansible/playbooks/runtime-seed.yaml` SHALL invoke the installed `dotfiles-runtime` binary from
`runtime_seed_bin_dir` (uv's tool bin dir). It SHALL NOT invoke
`uv run --directory {{ composition_root }}/src/runtime` or read any composition source path.

Source: `runtime-consumption`; REQ-002; BUG-001.

#### Scenario: the seed uses the installed binary

- **WHEN** the `runtime-seed` playbook is parsed
- **THEN** the wallpaper-set argv starts with
  `{{ runtime_seed_bin_dir }}/dotfiles-runtime`, and the task remains
  `when: not ansible_check_mode`

#### Scenario: no composition source path remains

- **WHEN** `rg -n 'src/runtime|uv run --directory' ansible/playbooks/runtime-seed.yaml` runs
- **THEN** it exits 1 with no matches
