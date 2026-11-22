---
id: REQ-065
title: "Pin assets v0.22.3 (wallpaper look-frame radius)"
kind: requirement
status: done
lane: direct
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-065/
branch: ticket/REQ-065-assets-v0223
---

# Pin assets v0.22.3

Mirror assets v0.22.3 (the app-owned look-frame takes
`surface.control.radius` from the skin) in every engine role and fixture.
Release the engine as v0.1.97.

## Closure (2026-11-21)

- Assets v0.22.3 mirrored in every engine role, fixture and the composition
  fixture; released as `v0.1.97` (`f9a0fdb`), tag pushed.
- Full `make gates` RC 0: test 1145 passed / 3 skipped; hermetic 1110 passed /
  38 skipped; ruff clean; `uv lock --check` clean.
- Consumed by composition REQ-137 (`v0.2.10`).
