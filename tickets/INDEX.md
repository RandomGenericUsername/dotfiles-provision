# Ticket index

> Counting rule: completeness checks cover item files (`tickets/<id>-<slug>/ticket.md`) only.
> `tickets/_template/` (and any `tickets/_fixtures/`) are excluded from INDEX completeness counting.
> Entry format: link — title | `status` | execution links. Epics add `done/total children done`, done-when, and one nested line per child. Bugs add severity. Spikes add timebox state.

## Active epics

(none)

## Requirements

(none)

## Bugs

- [BUG-003-consume-ags-apps-v042/ticket.md](./BUG-003-consume-ags-apps-v042/ticket.md) — consume ags-apps v0.4.2 (color thumbnails) + release v0.1.12 | severity: low | `in-progress` | worktree .worktrees/BUG-003

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
