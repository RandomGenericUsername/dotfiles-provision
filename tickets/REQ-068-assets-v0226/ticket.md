---
id: REQ-068
title: "Pin assets v0.22.6 (neutral Bluetooth full-signal badge)"
kind: requirement
status: done
lane: direct
worktree: .worktrees/REQ-068-assets-v0226/
branch: ticket/REQ-068-assets-v0226
---

# Pin assets v0.22.6

Mirror assets v0.22.6 (the Bluetooth full-signal badge uses the same neutral
container as good/medium/low). Release the engine as v0.1.100.

## Closure (2026-11-25)

- Released as `v0.1.100` (`3cc295f`); tag pushed; tool reinstalled.
- Pin-only gates (`make gates-pin`) RC 0; pin-audit, lint, docs-check and CI
  parity pass.
- Assets v0.22.6 makes the Bluetooth full-signal badge use the same neutral
  container as good/medium/low; the bar remains v0.6.35.
- Consumed by composition REQ-141 (`v0.2.13`).
