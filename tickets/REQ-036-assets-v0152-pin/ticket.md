---
id: REQ-036
title: "Mirror dotfiles-assets v0.15.2 and add the local pin-only gate lane"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-036/
branch: ticket/REQ-036-assets-v0152-pin
---

# Mirror dotfiles-assets v0.15.2 and add the local pin-only gate lane

## Requirement

`dotfiles-assets v0.15.2` maps wlogout buttons to card fill and panel-aligned
geometry. Mirror it in every engine assets pin/fixture and add a documented
local **pin-only** gate lane so version/fixture corrections no longer require
the 80–90 minute full `test` + `hermetic` cycle.

`gates-pin` runs: pin-audit, lint, docs-check and CI-gates parity, plus the fast
wlogout render test. Full `make gates` remains required for behavior/schema
changes. The pin-audit checks every role mirror, the fixture tuple and the
seven-app inventory against the composition fixture.

## Acceptance

- [ ] Every engine assets pin/mirror and fixture moves to `v0.15.2`.
- [ ] `scripts/pin-audit.py` passes; `make gates-pin` is documented and
      executable.
- [ ] Fast wlogout render test passes with the existing 3-variable context.
- [ ] Engine `0.1.54`, annotated tag `v0.1.54`, release with only wheel/sdist;
      no apply.
- [ ] Full `make gates` remains the policy for behavior/schema releases; this
      ticket records that the pin-only lane was used.

## Evidence / Verify

`python3 scripts/pin-audit.py`, `make gates-pin`, targeted wlogout render test.
