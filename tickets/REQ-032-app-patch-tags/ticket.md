---
id: REQ-032
title: "Mirror the seven v3 app patch releases in the engine fixtures"
kind: requirement
status: in-progress
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

- [ ] `tests/fixtures/ags-apps/app-list/all-standalone.apps.yaml` and
      `tests/fixtures/composition/dotfiles/provisioning/apps.yaml` pin the
      seven patch tags above, with their header comments naming the same
      inventory (repos stay fixture placeholders).
- [ ] `tests/unit/test_ags_apps_units_role.py` (including the final-tag
      inventory and hardcoded cutover assertions) and any other final-tag
      assertion name the patch tags; no stale final app-tag literal remains
      outside historical tickets/CHANGELOG.
- [ ] Fixture tags match the seven patch tags; lane/supervision fields
      (`launch`, `autostart`, ownership, links) are unchanged.
- [ ] Platform `v1.0.1`, contracts `v0.8.0`, assets `v0.13.0`, generation
      verify `version: 3` and the v3 locality tests are unchanged.
- [ ] Targeted AGS/verify/locality tests, `make gates` and
      `make ci-gates-parity` pass.
- [ ] Engine `0.1.49` + CHANGELOG, annotated tag `v0.1.49` after the
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
