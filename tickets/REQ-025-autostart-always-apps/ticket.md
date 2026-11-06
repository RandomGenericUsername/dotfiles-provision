---
id: REQ-025
title: "Verify always-on AGS apps by unit ownership, not autostart"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-025/
branch: ticket/REQ-025-autostart-always-apps
---

# Verify always-on AGS apps by unit ownership, not autostart

## Requirement

The v0.1.38 live apply failed at
`ags_apps_units : bar : assert autostart launches the identity once under the
shared lock`. `dotfiles-assets v0.12.1` correctly removed the `ags`
(`bar`) and `notifications` launch lines from
`configs/hypr/autostart.lua`: those always-on apps are now owned by the
`dotfiles-ags-bar.service` / `dotfiles-ags-notifications.service` systemd
`--user` units (REQ-023). The installer surface verification still demanded
exactly one `--expect-instance <autostart>` occurrence for every entry with an
`autostart` field, so a correct assets cutover can never pass.

The launch policy must decide the autostart contract:

- `launch: always` — the systemd `--user` unit exists and is enabled, and the
  assets-owned autostart file contains **zero** occurrences of
  `--expect-instance <autostart>` (the always-on app is never launched by
  autostart).
- `launch: on-demand` — an entry that declares an `autostart` identity keeps
  exactly **one** occurrence through `ags-run-locked` (capture, clipboard).

Provisioning never writes the assets-owned autostart content. The `verify`
mirror must apply the same split.

## Acceptance

- [ ] `ags_apps_units/tasks/_verify_surfaces.yml` asserts zero
      `--expect-instance <autostart>` occurrences for `launch: always` and the
      installed/enabled systemd unit, and exactly one `ags-run-locked`
      occurrence for `launch: on-demand`.
- [ ] The failure messages and comments describe the AD-32/assets v0.12.1
      epoch: units own always-on apps, autostart owns only launch-on-login
      overlays.
- [ ] The autostart stat/read/assert tasks are guardable by `app.launch`; no
      remaining assumption requires an always-on app in autostart.
- [ ] The `verify` mirror (`_verify_standalone.yml`) applies the same split.
- [ ] `tests/unit/test_ags_apps_units_role.py` fixtures use the actual assets
      v0.12.1 autostart shape (no `ags`/`notifications` lines) and cover:
      always zero + enabled unit passes, always with an autostart line fails,
      on-demand one occurrence passes, on-demand missing fails.
- [ ] `tests/unit/test_verify_role.py` fixtures/tests cover the same branches.
- [ ] `make gates`, `make ci-gates-parity`, and the targeted tests pass.
- [ ] Engine `0.1.39` + CHANGELOG; annotated tag `v0.1.39` after the
      fast-forward merge; push `main` and the tag; no apply.

## Evidence / Verify

Worktree `.worktrees/REQ-025/`, branch
`ticket/REQ-025-autostart-always-apps`.

(Filled in by the implementation and evidence commits.)
