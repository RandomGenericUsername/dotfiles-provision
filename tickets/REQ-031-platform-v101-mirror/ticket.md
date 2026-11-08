---
id: REQ-031
title: "Mirror ags-platform v1.0.1 in the engine pins"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-031/
branch: ticket/REQ-031-platform-v101-mirror
---

# Mirror ags-platform v1.0.1 in the engine pins

## Requirement

The `ags-platform` patch release **v1.0.1** fixes the appearance CSS
hex-literal validation: an ID selector (e.g. `#panel { … }`) is no longer
false-positived as a literal hex colour, while real hex literals are still
detected. The `dotfiles-v3` composition tuple moves to
`ags-platform: v1.0.1`, but the engine still installs and verifies `v1.0.0`.

Every platform pin mirror — the role, the verify mirror, the composition
fixture and the tests that stand in for a host — must move to `v1.0.1`. The
unit dir, pin file and shared shortcut stay derived from the one version var.
`contracts: v0.8.0`, `dotfiles-assets: v0.13.0` and the current v3 app tags
(bar `v0.6.0`, notifications `v0.5.0`, capture `v0.7.0`, clipboard `v0.6.0`,
wallpaper-selector/icme/btop-theme-studio `v0.5.0`) are unchanged, and
`dotfiles-v3` is not edited here.

## Acceptance

- [ ] `ansible/roles/ags_platform/vars/main.yml`: `ags_platform_version` is
      `v1.0.1`; the unit dir, pin file and shared shortcut still derive from
      that one var.
- [ ] `ansible/roles/verify/vars/main.yml`: `verify_ags_platform_version` is
      `v1.0.1`; unit dir/pin/shortcut remain derived, with no stale literal.
- [ ] Composition fixture `program-tuple.yaml`: `ags-platform: v1.0.1`,
      `contracts: v0.8.0`, `dotfiles-assets: v0.13.0`.
- [ ] Unit tests that stand in for a host (`test_ags_platform_role.py`,
      `test_ags_apps_units_role.py`, `test_verify_role.py`) use `v1.0.1`; no
      hardcoded `v1.0.0` platform fixture/simulation literal remains.
- [ ] Contracts remain `v0.8.0`, generation verify remains `version: 3`, and
      the v3 generation/locality tests pass unchanged.
- [ ] Targeted AGS/verify tests, `make gates` and `make ci-gates-parity` pass.
- [ ] Engine `0.1.48` + CHANGELOG, annotated tag `v0.1.48` after the
      fast-forward merge; push `main` and the tag; GitHub Release carries only
      the 0.1.48 sdist and wheel; no apply.

## Non-goals

- No `dotfiles-v3` file, runtime pin, assets pin, contract tag or live host is
  changed here.
- No v3 locality behaviour, generation schema or verify gate is relaxed.

## Evidence / Verify

Worktree `.worktrees/REQ-031/`, branch
`ticket/REQ-031-platform-v101-mirror`. Commits: plan (this file), then
implementation/release metadata, then evidence. Annotated tag `v0.1.48` created
on the fast-forward merge commit; no apply was run.
