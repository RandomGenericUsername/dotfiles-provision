# power-options (delta)

## ADDED Requirements

### Requirement: power profiles keep Bluetooth available

The engine SHALL rewrite `block_bt = false` in the `power-options` profiles
`Powersave++.toml`, `Powersave.toml` and `Balanced.toml` during bootstrap, restart the daemon and
refresh the active profile only when a file changed, and skip the step when
`/etc/power-options/profiles` is absent.
`verify` SHALL read the same profiles and fail when any still carries `block_bt = true`.

Source: REQ-003; `/etc/power-options/profiles/*.toml`.

#### Scenario: the blocking profiles are rewritten

- **WHEN** the `power_options` role runs on a host with `/etc/power-options/profiles`
- **THEN** the three profiles carry `block_bt = false`, and the run is idempotent

#### Scenario: a package update restores the block

- **WHEN** one profile again carries `block_bt = true`
- **THEN** `verify` fails naming the profile; re-running the power-options playbook fixes it

#### Scenario: non-Arch host

- **WHEN** `/etc/power-options/profiles` is absent
- **THEN** the role mutates nothing and verify skips the check
