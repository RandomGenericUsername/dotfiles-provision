---
id: REQ-027
title: "Pin the final seven-app AGS release tags in the engine fixtures"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-027/
branch: ticket/REQ-027-final-app-tags
---

# Pin the final seven-app AGS release tags

## Requirement

The `dotfiles-v3` `deploy-coverage` gate composes the final all-standalone
epoch against the engine's seven-app fixture. New per-app releases landed
since engine v0.1.40:

| app | repo | final tag |
| --- | --- | --- |
| bar | ags-bar | `v0.5.0` |
| notifications | ags-notifications | `v0.4.0` |
| capture | ags-capture-tool | `v0.6.1` |
| clipboard | ags-clipboard | `v0.5.0` |
| wallpaper-selector | ags-wallpaper-selector | `v0.4.1` |
| icme | ags-icme | `v0.4.1` |
| btop-theme-studio | ags-btop-theme-studio | `v0.4.1` |

The engine's final app-list fixture, the composition fixture and the
unit/verify simulations must state this inventory exactly, so a composition
pinned to the new releases cannot disagree with the engine's final topology.
Seed/legacy fixtures that intentionally model older generations stay
unchanged.

## Acceptance

- [ ] `tests/fixtures/ags-apps/app-list/all-standalone.apps.yaml` and
      `tests/fixtures/composition/dotfiles/provisioning/apps.yaml` pin the
      seven final tags above (repos stay fixture placeholders).
- [ ] `test_ags_apps_units_role.py` execution helpers create each fake app
      repo at its fixture tag and assert installs/pins/tag bumps against
      `entry["tag"]`; no stale `v0.1.0` topology assumption remains.
- [ ] `test_verify_role.py`'s provisioned-layout simulation builds every AGS
      unit from the fixture tag, with a test asserting the final seven-app
      inventory tags are exactly the table above.
- [ ] Targeted AGS/verify tests, `make gates` and `make ci-gates-parity` pass.
- [ ] Engine `0.1.41` + CHANGELOG; annotated tag `v0.1.41` after the
      fast-forward merge; push `main` and the tag; no apply.

## Evidence / Verify

Worktree `.worktrees/REQ-027/`, branch
`ticket/REQ-027-final-app-tags`.

(Filled in by the implementation and evidence commits.)
