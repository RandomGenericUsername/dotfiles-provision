---
id: REQ-064
title: "Pin assets v0.22.2 (paint-only wallpaper skin, surface.panel)"
kind: requirement
status: in-progress
lane: direct
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-064/
branch: ticket/REQ-064-assets-v0230
---

# Pin assets v0.22.2

Mirror the composition's assets v0.22.2 pin in every engine role and verify
expectation. v0.22.2 is the established paint-only wallpaper skin: the overlay
uses `surface.panel` (host-delegated geometry), not a separate overlay role.
Release the engine as v0.1.96.
