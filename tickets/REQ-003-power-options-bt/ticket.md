---
id: REQ-003
title: "Keep Bluetooth enabled across power-options profiles"
kind: requirement
status: done
lane: 2
links:
  openspec: power-options-bt
  bmad: none
worktree: .worktrees/req-003/
branch: ticket/req-003-power-options-bt
---

# Keep Bluetooth enabled across power-options profiles

## Requirement

`power-options-daemon` applies `block_bt = true` in its `Powersave++`, `Powersave` and `Balanced`
profiles (and `false` only in `Performance`/`Performance++`). The engine SHALL rewrite that flag to
`false` in the three blocking profiles during bootstrap, refresh the active profile when a file
changed, and verify the deployed files so a package update cannot silently restore the block.

This is an engine role/playbook slice; the composition only bumps the installer pin.

## Acceptance

- [x] New `power_options` role with `power_options_profile_dir` and the three profile names; the
  `replace` task flips `^block_bt = true$` → `block_bt = false` and is idempotent.
- [x] `power-options.yaml` runs with `become: true`; `bootstrap.yaml` imports it after `packages`.
- [x] The role's `refresh-full` runs only when a profile changed.
- [x] The role is a no-op when `/etc/power-options/profiles` is absent (non-Arch).
- [x] `verify` reads the same three profiles and fails when any still says `block_bt = true`.
- [x] Unit tests + full engine gates green; `v0.1.10` tagged/released; composition pin bumped.

## Out of scope

- Changing `power-options-daemon` itself or its package.
- Wi-Fi/NFC radio policy.
- The user-level GUI config; this edits the package-owned `/etc` profile files.

## Closeout

| Claim | Command | Result |
| --- | --- | --- |
| Engine release | `gh run view 40150940329`; `gh release view v0.1.11 --json assets` | tag CI `completed/success` incl. `release`; wheel + sdist |
| Profiles rewritten | `grep -H '^block_bt' /etc/power-options/profiles/*.toml` | all five profiles `false` |
| Marker | `cat /etc/power-options/.dotfiles-bt-ok` | present (`block_bt = false`) |
| Live Powersave | `power-daemon-mgr set-profile-override Powersave`; `rfkill list bluetooth`; `bluetoothctl show` | `Soft blocked: no`, `Powered: yes`, `PowerState: on` |
| Live Balanced | `power-daemon-mgr set-profile-override Balanced`; same checks | `Soft blocked: no`, `Powered: yes` |
| Daemon reload | reboot at 2026-10-25 16:33; `journalctl -u power-options` | applied Performance + `rfkill unblock bluetooth`; subsequent Powersave/Balanced applied with no block |
| Full verify | `make provision ARGS="verify --expected-engine-tag v0.1.11"` (from `dotfiles-v3`) | exit 0; all tasks ok, including the power-options check |

The v0.1.11 restart task was proven by the role unit test and the live reboot reload. The current host still has the v0.1.10 marker content; the next bootstrap writes `policy_version = 2` and restarts once. Behaviour is correct now.
