# power-options-bt

## Why

`power-options-daemon` blocks the Bluetooth radio (`block_bt = true`) in every profile except
Performance/Performance++. Switching to Powersave or Balanced therefore soft-blocks the controller,
and the settings-panel toggle becomes a silent no-op. The user wants Bluetooth available in every
profile.

Evidence: `/etc/power-options/profiles/{Powersave,Powersave++,Balanced}.toml` carry
`block_bt = true`; `Performance.toml` carries false; the daemon journal logs
`rfkill block set for type bluetooth` when Balanced is applied and `unblock` for Performance.
Verify: `grep -H block_bt /etc/power-options/profiles/*.toml`.

## What Changes

- New engine role `power_options`: stat `/etc/power-options/profiles`, assert the three profiles
  exist, `replace` `^block_bt = true$` → `block_bt = false`, and run
  `power-daemon-mgr refresh-full` only when a file changed.
- New `power-options.yaml` playbook (`become: true`); imported in `bootstrap.yaml` after
  `packages.yaml`.
- `verify` reads the same three profiles and asserts `block_bt = false`; the check is skipped when
  the profile directory is absent (non-Arch).
- Unit tests; engine `v0.1.10`; composition `installer.pin` bump.

## Capabilities

- **New Capabilities:** `power-options` — the power-profile Bluetooth policy.

## Non-goals

- Changing the daemon, profiles' CPU/GPU/network settings, or Wi-Fi/NFC policy.
- A GUI change; the role edits the package-owned TOML files.

## Impact

- New: `ansible/roles/power_options/`, `ansible/playbooks/power-options.yaml`,
  `tests/unit/test_power_options_role.py`, ticket + OpenSpec change.
- Modified: `ansible/playbooks/bootstrap.yaml`, `ansible/roles/verify/{vars,tasks}/main.yml`,
  `tests/unit/test_bootstrap_playbook.py`, `pyproject.toml`, `CHANGELOG.md`.
- Composition: `installer.pin` → `v0.1.10`; no assets/CLI changes.
