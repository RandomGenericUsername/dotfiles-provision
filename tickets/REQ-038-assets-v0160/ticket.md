---
id: REQ-038
title: "Mirror dotfiles-assets v0.16.0 (terminal-host skin)"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-038/
branch: ticket/REQ-038-assets-v0160
---

# Mirror dotfiles-assets v0.16.0 (terminal-host skin)

## Requirement

Assets v0.16.0 adds the opt-in `terminal-host` skin. Mirror the assets pin,
include the fifth manifest in verify expectations, and release through
`gates-pin`.

## Acceptance

- [x] Every assets mirror/fixture is v0.16.0.
- [x] `verify_skins_manifest_names` includes `terminal-host`.
- [x] `pin-audit`/`gates-pin` pass; engine 0.1.58 tagged/released; no apply.
