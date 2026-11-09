---
id: REQ-032
title: "Mirror the seven v3 app patch releases in the engine fixtures"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-032/
branch: ticket/REQ-032-app-patch-tags
---

# Mirror the seven v3 app patch releases in the engine fixtures

## Requirement

All seven standalone AGS app repos shipped patch releases onto the
`ags-platform` **v1.0.1** line, with no app behaviour changes:

| app | repo | final tag |
| --- | --- | --- |
| bar | ags-bar | `v0.6.1` |
| notifications | ags-notifications | `v0.5.1` |
| capture | ags-capture-tool | `v0.7.1` |
| clipboard | ags-clipboard | `v0.6.1` |
| wallpaper-selector | ags-wallpaper-selector | `v0.5.1` |
| icme | ags-icme | `v0.5.1` |
| btop-theme-studio | ags-btop-theme-studio | `v0.5.1` |

The engine's final all-standalone app-list fixture, the composition fixture
and the host-stand-in assertions still name the previous v3 tags. They must
state the new seven-app inventory exactly so a composition pinned to the
patch releases cannot disagree with the engine's final topology.

`ags-platform: v1.0.1`, `contracts: v0.8.0`, `dotfiles-assets: v0.13.0`,
the v3 generation/locality behaviour and all source roles are unchanged.
`dotfiles-v3` is not edited here.

## Acceptance

- [x] `tests/fixtures/ags-apps/app-list/all-standalone.apps.yaml` and
      `tests/fixtures/composition/dotfiles/provisioning/apps.yaml` pin the
      seven patch tags above, with their header comments naming the same
      inventory (repos stay fixture placeholders).
- [x] `tests/unit/test_ags_apps_units_role.py` (including the final-tag
      inventory and hardcoded cutover assertions) and any other final-tag
      assertion name the patch tags; no stale final app-tag literal remains
      outside historical tickets/CHANGELOG.
- [x] Fixture tags match the seven patch tags; lane/supervision fields
      (`launch`, `autostart`, ownership, links) are unchanged.
- [x] Platform `v1.0.1`, contracts `v0.8.0`, assets `v0.13.0`, generation
      verify `version: 3` and the v3 locality tests are unchanged.
- [x] Targeted AGS/verify/locality tests, `make gates` and
      `make ci-gates-parity` pass.
- [x] Engine `0.1.49` + CHANGELOG, annotated tag `v0.1.49` after the
      fast-forward merge; push `main` and the tag; GitHub Release carries only
      the 0.1.49 sdist and wheel; no apply.

## Non-goals

- No `dotfiles-v3` file, runtime pin, assets pin, platform pin, contract tag
  or live host is changed here.
- No v3 locality behaviour, generation schema or verify gate is relaxed.

## Evidence / Verify

Worktree `.worktrees/REQ-032/`, branch
`ticket/REQ-032-app-patch-tags`. Commits: plan (this file), then
implementation/release metadata, then evidence. Annotated tag `v0.1.49` created
on the fast-forward merge commit; no apply was run.

## Gate evidence

Implementation: `50e6249` (`feat(REQ-032): mirror v3 app patch tags; release
0.1.49`). Fixture diff changes only the seven final tags + header comments +
host-stand-in assertions; lane/supervision/ownership fields are untouched.

- `make test` → **1005 passed, 3 skipped, 60 deselected** in 2741.15s
- `make lint` → **All checks passed**
- `make hermetic` → **974 passed, 34 skipped, 60 deselected** in 2841.15s
- `make lock-check` → **Resolved 33 packages**
- `make docs-check` → exit 0
- `make ci-gates-parity` →
  `PASS gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test']`
- Final fixture tags are exactly bar `v0.6.1`, notifications `v0.5.1`,
  capture `v0.7.1`, clipboard `v0.6.1`, wallpaper-selector/icme/
  btop-theme-studio `v0.5.1`; platform `v1.0.1`, contracts `v0.8.0`, assets
  `v0.13.0`, generation verify `version: 3` unchanged.
- Release: engine `0.1.49`, annotated tag `v0.1.49`, GitHub Release with only
  the 0.1.49 sdist/wheel; layered gates were restarted after an external
  termination of the first hermetic process and completed green on the same
  commit.
