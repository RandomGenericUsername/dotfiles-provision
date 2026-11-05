---
id: OPS-002
title: "Sync REQ-016/REQ-017 INDEX status with their shipped tags"
kind: ops-task
status: done
lane: direct
links:
  openspec: none
  bmad: none
worktree: .worktrees/OPS-002/
branch: ticket/OPS-002-index-status-sync
---

# Sync REQ-016/REQ-017 INDEX status with their shipped tags

## Work

Both requirements are `done` in their ticket frontmatter with all acceptance
boxes ticked, and their releases shipped, but `tickets/INDEX.md` still said
`in-progress`:

- `REQ-016-retire-csg` → engine `v0.1.30`, deployed with PIN-0122.
- `REQ-017-ags-platform-v040` → engine `v0.1.31`, deployed with PIN-0123.

Update both INDEX lines to `done` with their tags and deployment pins.

## Done-when

The REQ-016/REQ-017 INDEX lines match the ticket frontmatter and the shipped
engine tags.

## Evidence

- `git tag --sort=-creatordate` → `v0.1.30`, `v0.1.31`.
- Each ticket's `## Outcome` section.
- `tickets/INDEX.md` — `done`, tag + deployment pin.
