---
id: REQ-030
title: "Mirror the final v3 composition: ags-platform v1.0.0 and v3 app tags"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-030/
branch: ticket/REQ-030-v3-final-mirrors
---

# Mirror the final v3 composition: ags-platform v1.0.0 and v3 app tags

## Requirement

The `dotfiles-v3` final composition moves the shared platform to
`ags-platform: v1.0.0` and pins the next released generation of every
standalone AGS app:

| app | final v3 tag |
| --- | --- |
| bar | `v0.6.0` |
| notifications | `v0.5.0` |
| capture | `v0.7.0` |
| clipboard | `v0.6.0` |
| wallpaper-selector | `v0.5.0` |
| icme | `v0.5.0` |
| btop-theme-studio | `v0.5.0` |

The engine must install and verify that platform tag, and its final app-list
fixture, composition fixture and host simulation must state that seven-app
inventory exactly. The v0.1.43 Generations v3 work is preserved: contracts
stay `v0.8.0`, verify keeps `generation_manifest_version: 3` and the stable
consumer-link/immutable-tag checks. `dotfiles-v3` is not edited here.

## Acceptance

- [ ] `ansible/roles/ags_platform/vars/main.yml` pins
      `ags_platform_version: v1.0.0`; the unit dir, pin file and shared
      shortcut still derive from that one var.
- [ ] `ansible/roles/verify/vars/main.yml` mirrors
      `verify_ags_platform_version: v1.0.0`; unit dir/pin/shortcut remain
      derived, with no stale literal.
- [ ] Composition fixture `program-tuple.yaml` reads
      `ags-platform: v1.0.0`, keeps `contracts: v0.8.0` and
      `dotfiles-assets: v0.13.0`.
- [ ] `tests/fixtures/ags-apps/app-list/all-standalone.apps.yaml` and
      `tests/fixtures/composition/dotfiles/provisioning/apps.yaml` pin the
      seven v3 tags above (repos stay fixture placeholders).
- [ ] Unit tests that stand in for a host (`test_ags_platform_role.py`,
      `test_ags_apps_units_role.py`, `test_verify_role.py`) use `v1.0.0` and
      the v3 app inventory; no stale `v0.9.1` or v2 app-tag literal remains.
- [ ] Contracts remain `v0.8.0`, generation verify remains `version: 3`, and
      the v0.1.43 locality tests pass unchanged.
- [ ] Targeted AGS/verify tests, `make gates` and `make ci-gates-parity` pass.
- [ ] Engine `0.1.44` + CHANGELOG, annotated tag `v0.1.44` after the
      fast-forward merge; push `main` and the tag; no apply.

## Non-goals

- No `dotfiles-v3` file, runtime pin, assets pin, contract tag or live host is
  changed here.
- No v3 locality behaviour, generation schema or verify gate is relaxed.

## Evidence / Verify

Worktree `.worktrees/REQ-030/`, branch
`ticket/REQ-030-v3-final-mirrors`. Evidence is recorded after the gates run.
