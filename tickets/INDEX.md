# Ticket index

> Counting rule: completeness checks cover item files (`tickets/<id>-<slug>/ticket.md`) only.
> `tickets/_template/` (and any `tickets/_fixtures/`) are excluded from INDEX completeness counting.
> Entry format: link — title | `status` | execution links. Epics add `done/total children done`, done-when, and one nested line per child. Bugs add severity. Spikes add timebox state.

## Active epics

(none)

## Requirements

- [REQ-018-assets-pin-v064/ticket.md](./REQ-018-assets-pin-v064/ticket.md) — Consume dotfiles-assets v0.6.4 (rofi/wlogout roles) | `done` | tag: v0.1.32 | live: rofi follows wallpaper
- [REQ-014-cli-tools-manifest-source/ticket.md](./REQ-014-cli-tools-manifest-source/ticket.md) — `cli_tools`: consume the composition manifest as the single pin source | `done` | tag: v0.1.28 | live: tpr/runtime v0.5.0 installed from manifest
- [REQ-015-assets-pin-v063/ticket.md](./REQ-015-assets-pin-v063/ticket.md) — Consume dotfiles-assets v0.6.3 (semantic-role icon mappings) | `done` | tag: v0.1.29 | live: assets v0.6.3, no colorN
- [REQ-016-retire-csg/ticket.md](./REQ-016-retire-csg/ticket.md) — Retire CSG from provisioning; tpr is the sole palette producer | `done` | tag: v0.1.30 | deployed PIN-0122
- [REQ-017-ags-platform-v040/ticket.md](./REQ-017-ags-platform-v040/ticket.md) — Bump ags-platform pin to v0.4.0 (theme-provider Phase A) | `done` | tag: v0.1.31 | deployed PIN-0123
- [REQ-019-ags-platform-v050/ticket.md](./REQ-019-ags-platform-v050/ticket.md) — Bump ags-platform pin to v0.5.0 (capture-cluster contract) | `done` | tag: v0.1.33 | worktree: .worktrees/REQ-019/ | branch: ticket/REQ-019-ags-platform-v050
- [REQ-020-skin-plane-deploy/ticket.md](./REQ-020-skin-plane-deploy/ticket.md) — Deploy the assets skin plane into the spine and expose the AGS skin pointers | `done` | tag: v0.1.34 | worktree: .worktrees/REQ-020/ | branch: ticket/REQ-020-skin-plane-deploy
- [REQ-021-skins-assets-v011/ticket.md](./REQ-021-skins-assets-v011/ticket.md) — Consume dotfiles-assets v0.11.0 (per-app skin templates) | `proposed` | worktree: .worktrees/REQ-021/ | branch: ticket/REQ-021-skins-assets-v011

## Bugs

- [BUG-003-consume-ags-apps-v042/ticket.md](./BUG-003-consume-ags-apps-v042/ticket.md) — consume ags-apps v0.4.2 (color thumbnails) + release v0.1.12 | severity: low | `done` | worktree .worktrees/BUG-003, branch ticket/BUG-003-consume-ags-apps-v042
- [BUG-004-sddm-wayland-greeter/ticket.md](./BUG-004-sddm-wayland-greeter/ticket.md) — SDDM Wayland greeter has no compositor (90 s session bounce) | severity: high | `done` | worktree .worktrees/BUG-004, branch ticket/BUG-004-sddm-wayland-greeter | tag: v0.1.13
- [BUG-005-sddm-logout-greeter-crash/ticket.md](./BUG-005-sddm-logout-greeter-crash/ticket.md) — Logout leaves a black VT; sddm-helper exits 1 and the greeter never restarts (5-login acceptance blocked) | severity: high | `done` | worktree .worktrees/BUG-005, branch ticket/BUG-005-sddm-logout-greeter-crash | resolved in assets v0.6.1 (engine v0.1.16, PIN-0115); 3/5 formal acceptance, user-waived
- [BUG-006-rofi-post-bootstrap-colors](./BUG-006-rofi-post-bootstrap-colors/ticket.md) — Rofi cannot launch after bootstrap until the first wallpaper set creates colors.rasi | severity: high | `done` | tag: v0.1.27
- [BUG-008-runtime-seed-producer-env](./BUG-008-runtime-seed-producer-env/ticket.md) — runtime-seed ignores the configured palette producer (single/double underscore mismatch) | severity: high | `done` | tag: v0.1.27
- [BUG-007-tpr-native-provisioning](./BUG-007-tpr-native-provisioning/ticket.md) — tpr native engine is not provisioned: bootstrap is green, first tpr wallpaper set fails | severity: high | `done` | tag: v0.1.27 | decided: container mode

## Requirements

- [REQ-010-tpr-producer-support](./REQ-010-tpr-producer-support/ticket.md) — Support tpr as a palette producer (pin + roles + verify) | `in-progress` | worktree: .worktrees/REQ-010/ | branch: ticket/REQ-010-tpr-producer-support

## Requirements

- [REQ-011-tpr-v020-pin](./REQ-011-tpr-v020-pin/ticket.md) — Pin theme-producer v0.4.0 | `done` | tag: v0.1.25

## Requirements

- [REQ-012-runtime-v040-pin](./REQ-012-runtime-v040-pin/ticket.md) — Pin dotfiles-runtime v0.4.0 (producer seam) | `done` | tag: v0.1.26

## Ops tasks

- [OPS-001-bootstrap-order-tpr-path](./OPS-001-bootstrap-order-tpr-path/ticket.md) — Fix bootstrap order and the tpr checkout path | `done` | worktree none, branch main | tag: v0.1.24
- [OPS-002-index-status-sync](./OPS-002-index-status-sync/ticket.md) — Sync REQ-016/REQ-017 INDEX status with their shipped tags | `done` | worktree: .worktrees/OPS-002/ | branch: ticket/OPS-002-index-status-sync

## Spikes

(none)

## Tasks

(none)

## Done (links only, newest last)

- [REQ-001-repo-birth](./REQ-001-repo-birth/ticket.md) — Birth the dotfiles-provision engine (mu-strict) with the composition seam and v0.1.0 | `done` | openspec: repo-birth (validated strictly)
- [REQ-002-runtime-repo-pin](./REQ-002-runtime-repo-pin/ticket.md) — Consume `dotfiles-runtime` as a pinned repo (engine v0.1.7) | `done` | openspec: runtime-repo-pin | tag: v0.1.7
- [REQ-003-power-options-bt](./REQ-003-power-options-bt/ticket.md) — Keep Bluetooth enabled across power-options profiles | `done` | openspec: power-options-bt | tag: v0.1.11
- [BUG-001-runtime-seed-installed](./BUG-001-runtime-seed-installed/ticket.md) — `runtime-seed` invokes the deleted composition `src/runtime` | `done` | openspec: runtime-seed-installed | tag: v0.1.8
- [BUG-002-group-vars-wheel](./BUG-002-group-vars-wheel/ticket.md) — Installed engine wheel drops `inventory/group_vars` | `done` | openspec: group-vars-wheel | tag: v0.1.9
- [REQ-005-consume-ags-apps-v043](./REQ-005-consume-ags-apps-v043/ticket.md) — Consume ags-apps v0.4.3 (selector collapses on Apply) + release v0.1.14 | `done` | openspec: none | tag: v0.1.14
- [REQ-006-mirror-runtime-v020](./REQ-006-mirror-runtime-v020/ticket.md) — Mirror runtime v0.2.0 in verify + release v0.1.15 | `done` | openspec: none | tag: v0.1.15
- [REQ-007-consume-assets-v061-runtime-v022](./REQ-007-consume-assets-v061-runtime-v022/ticket.md) — Consume assets v0.6.1 + runtime v0.2.2 in one pin release (engine v0.1.16) | `done` | openspec: none | tag: v0.1.16
- [REQ-009-consume-csg-v021-runtime-v023](./REQ-009-consume-csg-v021-runtime-v023/ticket.md) — Consume csg v0.2.1 + runtime v0.2.3 in one pin release (engine v0.1.17) | `done` | openspec: none | tag: v0.1.17
- [REQ-008-ags-app-install-topology](./REQ-008-ags-app-install-topology/ticket.md) — Generic per-app AGS install topology and one-owner cutover | `done` | worktree .worktrees/REQ-008, branch ticket/REQ-008-ags-app-install-topology | tags: v0.1.18 (topology), v0.1.19 (adoption tuple)
