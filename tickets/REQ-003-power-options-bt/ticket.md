---
id: REQ-003
title: "Keep Bluetooth enabled across power-options profiles"
kind: requirement
status: in-progress
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

- [ ] New `power_options` role with `power_options_profile_dir` and the three profile names; the
  `replace` task flips `^block_bt = true$` → `block_bt = false` and is idempotent.
- [ ] `power-options.yaml` runs with `become: true`; `bootstrap.yaml` imports it after `packages`.
- [ ] The role's `refresh-full` runs only when a profile changed.
- [ ] The role is a no-op when `/etc/power-options/profiles` is absent (non-Arch).
- [ ] `verify` reads the same three profiles and fails when any still says `block_bt = true`.
- [ ] Unit tests + full engine gates green; `v0.1.10` tagged/released; composition pin bumped.

## Out of scope

- Changing `power-options-daemon` itself or its package.
- Wi-Fi/NFC radio policy.
- The user-level GUI config; this edits the package-owned `/etc` profile files.
