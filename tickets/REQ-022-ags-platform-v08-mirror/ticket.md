---
id: REQ-022
title: "Mirror ags-platform v0.8.0 in the engine pins"
kind: requirement
status: proposed
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-022/
branch: ticket/REQ-022-ags-platform-v08-mirror
---

# Mirror ags-platform v0.8.0 in the engine pins

## Requirement

The final all-standalone apps require `ags-platform` v0.8.0 (the app-scoped
`createAppSkin` generation). The engine still installs and verifies `v0.5.0`,
so `dotfiles-v3` `make deploy-coverage` fails before provisioning:

`program-tuple.yaml: ags-platform 'v0.8.0' is not resolved by ansible/roles/ags_platform/vars/main.yml ags_platform_version = 'v0.5.0'`.

Every platform pin mirror — the role, the verify mirror, the composition
fixture and the tests that stand in for a host — must move to `v0.8.0`. The
same tuple moves `contracts` to `v0.6.0`; `dotfiles-assets` stays `v0.11.0`
and the skins verify plane is unchanged. `dotfiles-v3` is not edited here.

## Acceptance

- [ ] `ansible/roles/ags_platform/vars/main.yml`: `ags_platform_version` is
      `v0.8.0`; the unit dir, pin file and absence of a role-owned shortcut
      still derive from that one var.
- [ ] `ansible/roles/verify/vars/main.yml`: `verify_ags_platform_version` is
      `v0.8.0`; unit dir/pin/shortcut remain derived, with no stale literal.
- [ ] Composition fixture `program-tuple.yaml`: `ags-platform: v0.8.0`,
      `contracts: v0.6.0`, `dotfiles-assets: v0.11.0`.
- [ ] Unit tests that stand in for a host (`test_ags_platform_role.py`,
      `test_ags_apps_units_role.py`, `test_verify_role.py`) use `v0.8.0`.
- [ ] No unrelated `v0.5.0` asset/template comments change; assets stay
      `v0.11.0` and the skins verify plane is untouched.
- [ ] `make gates`, `make ci-gates-parity` and the AGS unit tests pass; a
      temporary `dotfiles-v3` copy with `installer.pin: v0.1.36` passes
      `make deploy-coverage` while its program tuple names `v0.8.0`.
- [ ] Engine `0.1.36` + CHANGELOG, annotated tag `v0.1.36` after the
      fast-forward merge; no push.

## Evidence / Verify

Evidence recorded when the implementation commit lands.
