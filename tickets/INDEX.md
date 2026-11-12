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
- [REQ-021-skins-assets-v011/ticket.md](./REQ-021-skins-assets-v011/ticket.md) — Consume dotfiles-assets v0.11.0 (per-app skin templates) | `done` | tag: v0.1.35 | worktree: .worktrees/REQ-021/ | branch: ticket/REQ-021-skins-assets-v011
- [REQ-022-ags-platform-v08-mirror/ticket.md](./REQ-022-ags-platform-v08-mirror/ticket.md) — Mirror ags-platform v0.8.0 in the engine pins | `done` | tag: v0.1.36 | worktree: .worktrees/REQ-022/ | branch: ticket/REQ-022-ags-platform-v08-mirror
- [REQ-023-appearance-supervision/ticket.md](./REQ-023-appearance-supervision/ticket.md) — Supervise the always-on AGS apps with systemd --user units | `done` | tag: v0.1.37 | worktree: .worktrees/REQ-023/ | branch: ticket/REQ-023-appearance-supervision
- [REQ-024-appearance-v2-mirrors/ticket.md](./REQ-024-appearance-v2-mirrors/ticket.md) — Mirror the dotfiles-v3 appearance v2 tuple in the engine | `done` | tag: v0.1.38 | worktree: .worktrees/REQ-024/ | branch: ticket/REQ-024-appearance-v2-mirrors
- [REQ-025-autostart-always-apps/ticket.md](./REQ-025-autostart-always-apps/ticket.md) — Verify always-on AGS apps by unit ownership, not autostart | `done` | tag: v0.1.39 | worktree: .worktrees/REQ-025/ | branch: ticket/REQ-025-autostart-always-apps
- [REQ-026-assets-v013-terminal/ticket.md](./REQ-026-assets-v013-terminal/ticket.md) — Consume dotfiles-assets v0.13.0 (terminal skin, cleanup layout removal) | `done` | tag: v0.1.40 | worktree: .worktrees/REQ-026/ | branch: ticket/REQ-026-assets-v013-terminal
- [REQ-027-final-app-tags/ticket.md](./REQ-027-final-app-tags/ticket.md) — Pin the final seven-app AGS release tags in the engine fixtures | `done` | tag: v0.1.41 | worktree: .worktrees/REQ-027/ | branch: ticket/REQ-027-final-app-tags
- [REQ-028-platform-v091-mirror/ticket.md](./REQ-028-platform-v091-mirror/ticket.md) — Mirror ags-platform v0.9.1 in the engine pins | `done` | tag: v0.1.42 | worktree: .worktrees/REQ-028/ | branch: ticket/REQ-028-platform-v091-mirror
- [REQ-029-generations-v3-locality/ticket.md](./REQ-029-generations-v3-locality/ticket.md) — Deploy v3 state locality: immutable app tags and stable consumer links | `done` | tag: v0.1.43 | worktree: .worktrees/REQ-029/ | branch: ticket/REQ-029-generations-v3-locality
- [REQ-030-v3-final-mirrors/ticket.md](./REQ-030-v3-final-mirrors/ticket.md) — Mirror the final v3 composition: ags-platform v1.0.0 and v3 app tags | `done` | tag: v0.1.44 | worktree: .worktrees/REQ-030/ | branch: ticket/REQ-030-v3-final-mirrors
- [REQ-031-platform-v101-mirror/ticket.md](./REQ-031-platform-v101-mirror/ticket.md) — Mirror ags-platform v1.0.1 in the engine pins | `done` | tag: v0.1.48 | worktree: .worktrees/REQ-031/ | branch: ticket/REQ-031-platform-v101-mirror
- [REQ-032-app-patch-tags/ticket.md](./REQ-032-app-patch-tags/ticket.md) — Mirror the seven v3 app patch releases in the engine fixtures | `done` | worktree: .worktrees/REQ-032/ | branch: ticket/REQ-032-app-patch-tags | tag: v0.1.49
- [REQ-033-skin-wlogout/ticket.md](./REQ-033-skin-wlogout/ticket.md) — Provision the wlogout appearance consumer link (SKIN-WLOGOUT slice) | `done` | worktree: .worktrees/REQ-033/ | branch: ticket/REQ-033-skin-wlogout | tag: v0.1.50
- [REQ-034-host-defaults-mirrors/ticket.md](./REQ-034-host-defaults-mirrors/ticket.md) — Mirror contracts v0.9.0 and assets v0.15.0 for the host-defaults cutover | `done` | worktree: .worktrees/REQ-034/ | branch: ticket/REQ-034-host-defaults-mirrors | tag: v0.1.51
- [REQ-035-assets-v0151/ticket.md](./REQ-035-assets-v0151/ticket.md) — Mirror dotfiles-assets v0.15.1 (wlogout static ownership fix) | `done` | worktree: .worktrees/REQ-035/ | branch: ticket/REQ-035-assets-v0151 | tag: v0.1.53
- [REQ-036-assets-v0152-pin/ticket.md](./REQ-036-assets-v0152-pin/ticket.md) — Mirror dotfiles-assets v0.15.2 and add the local pin-only gate lane | `done` | worktree: .worktrees/REQ-036/ | branch: ticket/REQ-036-assets-v0152-pin | tag: v0.1.56
- [REQ-039-skin-consumer-phase0/ticket.md](./REQ-039-skin-consumer-phase0/ticket.md) — Phase 0 hardening for the skin consumer plane (pin-audit + wlogout fallback) | `done` | worktree: .worktrees/REQ-039/ | branch: ticket/REQ-039-skin-consumer-phase0 | tag: v0.1.59
- [REQ-040-skin-consumer-phase3a4/ticket.md](./REQ-040-skin-consumer-phase3a4/ticket.md) — Phase 3A-4 format-aware skin consumers (GTK3/GTK4/rofi links + imports) | `done` | worktree: .worktrees/REQ-040/ | branch: ticket/REQ-040-skin-consumer-phase3a4 | tag: v0.1.60
- [REQ-041-host-rectangle-radii-pin/ticket.md](./REQ-041-host-rectangle-radii-pin/ticket.md) — Mirror contracts v0.11.0 and assets v0.18.0 (host rectangle radii) | `done` | worktree: .worktrees/REQ-041/ | branch: ticket/REQ-041-host-rectangle-radii-pin | tag: v0.1.61
- [REQ-042-assets-v0181-pin/ticket.md](./REQ-042-assets-v0181-pin/ticket.md) — Mirror dotfiles-assets v0.18.1 (rofi generated appearance last) | `done` | worktree: .worktrees/REQ-042/ | branch: ticket/REQ-042-assets-v0181-pin | tag: v0.1.62
- [REQ-043-window-kitty-platform-mirror/ticket.md](./REQ-043-window-kitty-platform-mirror/ticket.md) — Mirror contracts v0.12.0, assets v0.19.0, platform v1.1.0 and bar v0.6.2 (window role + kitty conf) | `done` | worktree: .worktrees/REQ-043/ | branch: ticket/REQ-043-window-kitty-platform-mirror | tag: v0.1.63
- [REQ-044-app-parity-inventory-pin/ticket.md](./REQ-044-app-parity-inventory-pin/ticket.md) — Mirror the parity app releases in the engine final inventory (bar v0.6.4; v0.6.3 is sound-panel) | `done` | worktree: .worktrees/REQ-044/ | branch: ticket/REQ-044-app-parity-inventory-pin | tag: v0.1.64

## Bugs

- [BUG-012-v0150-skins-contract-tag/ticket.md](./BUG-012-v0150-skins-contract-tag/ticket.md) — Verify rejects the assets v0.15.0 skins envelope because it still expects contracts v0.7.0 | severity: high | `done` | worktree .worktrees/BUG-012, branch ticket/BUG-012-v0150-skins-contract-tag | tag: v0.1.52
- [BUG-011-verify-consumer-link-assert-render/ticket.md](./BUG-011-verify-consumer-link-assert-render/ticket.md) — verify consumer-link assert reads `path`/`target` off a registered result dict and fails argument finalization | severity: high | `done` | worktree .worktrees/BUG-011, branch ticket/BUG-011-verify-consumer-link-assert-render | tag: v0.1.47
- [BUG-010-v3-seed-idempotent-tag-sweep/ticket.md](./BUG-010-v3-seed-idempotent-tag-sweep/ticket.md) — v3 cutover fails an idempotent seed and leaves runtime artifacts in historical app tags | severity: high | `done` | worktree .worktrees/BUG-010, branch ticket/BUG-010-v3-seed-idempotent-tag-sweep | tag: v0.1.46
- [BUG-009-unit-cutover-stop-start/ticket.md](./BUG-009-unit-cutover-stop-start/ticket.md) — v3 cutover leaves always-on AGS units on the previous tag (state: started is a no-op) | severity: high | `done` | worktree .worktrees/BUG-009, branch ticket/BUG-009-unit-cutover-stop-start | tag: v0.1.45
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
- [REQ-037-assets-v0153/ticket.md](./REQ-037-assets-v0153/ticket.md) — Mirror dotfiles-assets v0.15.3 (wlogout card-state correctness) | `done` | worktree: .worktrees/REQ-037/ | branch: ticket/REQ-037-assets-v0153 | tag: v0.1.57
- [REQ-038-assets-v0160/ticket.md](./REQ-038-assets-v0160/ticket.md) — Mirror dotfiles-assets v0.16.0 (terminal-host skin) | `done` | worktree: .worktrees/REQ-038/ | branch: ticket/REQ-038-assets-v0160 | tag: v0.1.58
- [REQ-039-skin-consumer-phase0/ticket.md](./REQ-039-skin-consumer-phase0/ticket.md) — Phase 0 hardening for the skin consumer plane (pin-audit + wlogout fallback) | `done` | worktree: .worktrees/REQ-039/ | branch: ticket/REQ-039-skin-consumer-phase0 | tag: v0.1.59
- [REQ-045-assets-v0200-pin/ticket.md](./REQ-045-assets-v0200-pin/ticket.md) — Mirror dotfiles-assets v0.20.0 (sound panel paint) | `done` | tag: v0.1.65 | worktree: .worktrees/REQ-045/ | branch: ticket/REQ-045-assets-v0200-pin
