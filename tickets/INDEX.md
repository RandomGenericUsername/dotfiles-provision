# Ticket index

> Counting rule: completeness checks cover item files (`tickets/<id>-<slug>/ticket.md`) only.
> `tickets/_template/` (and any `tickets/_fixtures/`) are excluded from INDEX completeness counting.
> Entry format: link — title | `status` | execution links. Epics add `done/total children done`, done-when, and one nested line per child. Bugs add severity. Spikes add timebox state.

## Active epics

(none)

## Requirements

(none)

## Bugs

- [BUG-003-consume-ags-apps-v042/ticket.md](./BUG-003-consume-ags-apps-v042/ticket.md) — consume ags-apps v0.4.2 (color thumbnails) + release v0.1.12 | severity: low | `done` | worktree .worktrees/BUG-003, branch ticket/BUG-003-consume-ags-apps-v042
- [BUG-004-sddm-wayland-greeter/ticket.md](./BUG-004-sddm-wayland-greeter/ticket.md) — SDDM Wayland greeter has no compositor (90 s session bounce) | severity: high | `done` | worktree .worktrees/BUG-004, branch ticket/BUG-004-sddm-wayland-greeter | tag: v0.1.13

## Ops tasks

(none)

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
