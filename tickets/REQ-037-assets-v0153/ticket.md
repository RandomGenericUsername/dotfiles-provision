---
id: REQ-037
title: "Mirror dotfiles-assets v0.15.3 (wlogout card-state correctness)"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-037/
branch: ticket/REQ-037-assets-v0153
---

# Mirror dotfiles-assets v0.15.3 (wlogout card-state correctness)

## Requirement

Assets v0.15.3 makes focused/hovered wlogout cards keep `surface.card.bg` and
use state ring/ink only. Mirror the assets pin and release through `gates-pin`.

## Acceptance

- [x] Every engine assets mirror/fixture is v0.15.3.
- [x] `pin-audit` and `gates-pin` pass; fast wlogout render passes.
- [x] Engine 0.1.57 tagged/released with only its wheel/sdist; no apply.
