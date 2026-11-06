---
id: REQ-028
title: "Mirror ags-platform v0.9.1 in the engine pins"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-028/
branch: ticket/REQ-028-platform-v091-mirror
---

# Mirror ags-platform v0.9.1 in the engine pins

## Requirement

The `dotfiles-v3` composition tuple now pins `ags-platform: v0.9.1` (palette
mode metadata, required by theme-producer v0.6.0 output), but the engine still
installs and verifies `v0.9.0`. `make deploy-coverage` fails before
provisioning:

`ansible/roles/ags_platform/vars/main.yml ags_platform_version = 'v0.9.0' does not resolve 'v0.9.1'`

Every platform pin mirror — the role, the verify mirror, the composition
fixture and the tests that stand in for a host — must move to `v0.9.1`. The
unit dir, pin file and shared shortcut stay derived from the one version var.
`contracts: v0.7.0` and `dotfiles-assets: v0.13.0` are unchanged, and
`dotfiles-v3` is not edited here.

## Acceptance

- [ ] `ansible/roles/ags_platform/vars/main.yml`: `ags_platform_version` is
      `v0.9.1`; the unit dir, pin file and shared shortcut still derive from
      that one var.
- [ ] `ansible/roles/verify/vars/main.yml`: `verify_ags_platform_version` is
      `v0.9.1`; unit dir/pin/shortcut remain derived, with no stale literal.
- [ ] Composition fixture `program-tuple.yaml`: `ags-platform: v0.9.1`,
      `contracts: v0.7.0`, `dotfiles-assets: v0.13.0`.
- [ ] Unit tests that stand in for a host (`test_ags_platform_role.py`,
      `test_ags_apps_units_role.py`, `test_verify_role.py`) use `v0.9.1`; no
      hardcoded `v0.9.0` fixture/simulation literal remains.
- [ ] Targeted AGS/verify tests, `make gates` and `make ci-gates-parity` pass;
      a temporary `dotfiles-v3` copy with `installer.pin: v0.1.42` passes
      `make deploy-coverage` while its program tuple names `v0.9.1`.
- [ ] Engine `0.1.42` + CHANGELOG, annotated tag `v0.1.42` after the
      fast-forward merge; push `main` and the tag; no apply.

## Evidence / Verify

Worktree `.worktrees/REQ-028/`, branch
`ticket/REQ-028-platform-v091-mirror`.

(Filled in by the implementation and evidence commits.)
