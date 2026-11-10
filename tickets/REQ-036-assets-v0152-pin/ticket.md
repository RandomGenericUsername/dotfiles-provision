---
id: REQ-036
title: "Mirror dotfiles-assets v0.15.2 and add the local pin-only gate lane"
kind: requirement
status: done
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

- [x] Every engine assets pin/mirror and fixture moves to `v0.15.2`.
- [x] `scripts/pin-audit.py` passes; `make gates-pin` is documented and
      executable.
- [x] Fast wlogout render test passes with the existing 3-variable context.
- [x] Engine `0.1.55`, annotated tag `v0.1.55`, release with only wheel/sdist;
      no apply.
- [x] Full `make gates` remains the policy for behavior/schema releases; this
      ticket records that the pin-only lane was used.

## Evidence

Implementation commit mirrors assets `v0.15.2`, adds `scripts/pin-audit.py` and
`make gates-pin`, and updates the fast wlogout render expectation. This is a
pin-only release; the full `make gates` suite was last green on `v0.1.53`.

- `make gates-pin` → rc 0:
  - `pin-audit: PASS (assets=v0.15.2, contracts=v0.9.0, platform=v1.0.1, apps=7)`
  - `ruff`: All checks passed
  - `docs-check`: rc 0
  - `ci-gates-parity`: PASS
- Fast wlogout render test: **11 passed, 6 skipped**.
- Release: engine `0.1.55`, annotated tag `v0.1.55`, GitHub Release with only
  its wheel/sdist; no apply.

The pin-only lane is now the documented local path for version/fixture-only
changes; behavior/schema changes continue to require full `make gates`.

Staging correction: the first commit for this ticket did not include the
pin/version files, so the initially cut `v0.1.54` tag built `0.1.53`. That tag is
left immutable but its release object is removed; `v0.1.55` is the corrected
pin-only release that includes assets `v0.15.2`.

## Evidence / Verify

`python3 scripts/pin-audit.py`, `make gates-pin`, targeted wlogout render test.
