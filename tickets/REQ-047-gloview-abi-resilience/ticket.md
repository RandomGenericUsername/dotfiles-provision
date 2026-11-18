---
id: REQ-047
title: "Own GloView activation with an observable user oneshot"
kind: requirement
status: done
lane: 2 — bounded correction
links:
  openspec: none
  bmad: none
  design: dotfiles-v3 docs/114-gloview-abi-resilience.md
worktree: .worktrees/REQ-047/
branch: ticket/REQ-047-gloview-abi-resilience
---

# Own GloView activation with an observable user oneshot

## Requirement

This is the engine half of composition **REQ-114**. GloView
(`/usr/lib/gloview.so`, `gloview-git` AUR) must degrade visibly and recoverably
when a Hyprland upgrade invalidates its ABI. Activation must be observable, and
the engine must never gain a privileged or automatic package-manager path.

The composition owns `gloview-activate`/`gloview-rebuild` and the guarded Hypr
binds; the engine installs and verifies the systemd surface.

## Work

- Install `dotfiles-gloview.service` as a user-scope `Type=oneshot`
  (`RemainAfterExit=yes`) ordered after `dbus.socket`,
  `graphical-session.target` and `dotfiles-ags-notifications.service`.
- Install the interactive `gloview-rebuild` helper (0755). It is user-run and
  is never the unit's `ExecStart`.
- Start the unit only inside an active graphical session; on a manager-less
  host, enable it through the graphical-session wants link.
- Add deferred `verify` coverage for the static contract: unit file, enabled
  link, `ExecStart` activator, `After=`/`WantedBy=` ordering, and the installed
  rebuild helper. Do not remove Lane A/UI verify checks.
- Mirror assets `v0.21.5` (GloView optional) across role/verify pins and the
  composition fixture.

## Criteria mapping

- **G-5**: unit scope/ordering and failed-state visibility.
- **G-6**: no `sudo`/`yay`/`pacman`/network in the unit or activator; helper is
  interactive and user-run.
- **G-7**: failure notification names `yay -S --rebuild gloview-git` plus the
  relog step; no automatic rebuild.

G-1…G-4 and G-8…G-10 are owned by the composition scripts/assets and are tested
in `dotfiles-v3` (`scripts/tests/test_gloview_abi.py`) plus this repo's
`tests/unit/test_gloview_units.py`.

## Acceptance

- [x] Unit template and handler exist and preserve the session ordering.
- [x] Role installs the unit and rebuild helper without `become` (except the
  legacy sudoers cleanup).
- [x] Activation is gated to a live graphical session; a TTY provision does not
  mark the oneshot active.
- [x] `verify` asserts the installed unit/link/ordering/activator and helper.
- [x] No second privileged or autostart activation path exists.
- [x] Full engine gates pass on `v0.1.84` + this change.

## Evidence

- Rebased onto engine `v0.1.84` (`dccbe13`); assets pin bumped to `v0.21.5`
  (`2b758f7`).
- `make gates`: test **1077 passed, 3 skipped**; lint **all checks passed**;
  hermetic **1042 passed, 38 skipped**; `uv lock --check` ok.
- Targeted `test_verify_role.py` + `test_gloview_units.py`: **132 passed, 22
  skipped**.
- Release tags: **`v0.1.85`** (initial), **`v0.1.86`** (quoted-`ExecStart` fix) and **`v0.1.87`** (rebuild-as-ExecStart check narrowed); both bugs found by apply.

## Residual

The failure notification names the exact command and relog step but does not
implement a clickable action (`notify-send` action) that opens a terminal. That
limitation is documented rather than omitted; the user runs `gloview-rebuild`
from a terminal.
