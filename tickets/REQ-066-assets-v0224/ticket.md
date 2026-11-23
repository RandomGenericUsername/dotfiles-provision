---
id: REQ-066
title: "Pin assets v0.22.4 (clipboard overlay skin)"
kind: requirement
status: done
lane: direct
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-066/
branch: ticket/REQ-066-assets-v0224
---

# Pin assets v0.22.4

Mirror assets v0.22.4 (clipboard overlay paint-only skin on `surface.panel`,
base v0.22.3) in every engine role, fixture and composition fixture. Release
the engine as v0.1.98.

## Closure (2026-11-23)

Released as **v0.1.98**. Assets v0.22.4 mirrored in every active engine role,
fixture and composition fixture. Gates:
- test: 1113 passed / 35 skipped (90 deselected)
- lint: ruff clean
- hermetic: 1110 passed / 38 skipped (90 deselected), exit 0
- lock-check: clean
- docs-check: clean

Consumed by composition REQ-138 (`v0.2.11`).
