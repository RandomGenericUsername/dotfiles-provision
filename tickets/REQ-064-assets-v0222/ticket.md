---
id: REQ-064
title: "Pin assets v0.22.2 (paint-only wallpaper skin, surface.panel)"
kind: requirement
status: done
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

## Closure (2026-11-20)

- Engine `v0.1.96` tagged and pushed (`2c342b9`); assets pin `v0.22.2`.
- Tests: `1113 passed, 35 skipped`; hermetic `1110 passed, 38 skipped` (RC 0);
  ruff clean. The historical-tag role test's Ansible timeout was widened
  240 s -> 600 s for cold hermetic hosts; assertions unchanged.
- Consumed by composition `v0.2.9`; live apply `ok=1164 changed=25 failed=0`,
  verify 0, doctor clean.
