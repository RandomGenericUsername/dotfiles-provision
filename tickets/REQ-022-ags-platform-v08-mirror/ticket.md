---
id: REQ-022
title: "Mirror ags-platform v0.8.0 in the engine pins"
kind: requirement
status: done
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

- [x] `ansible/roles/ags_platform/vars/main.yml`: `ags_platform_version` is
      `v0.8.0`; the unit dir, pin file and absence of a role-owned shortcut
      still derive from that one var.
- [x] `ansible/roles/verify/vars/main.yml`: `verify_ags_platform_version` is
      `v0.8.0`; unit dir/pin/shortcut remain derived, with no stale literal.
- [x] Composition fixture `program-tuple.yaml`: `ags-platform: v0.8.0`,
      `contracts: v0.6.0`, `dotfiles-assets: v0.11.0`.
- [x] Unit tests that stand in for a host (`test_ags_platform_role.py`,
      `test_ags_apps_units_role.py`, `test_verify_role.py`) use `v0.8.0`.
- [x] No unrelated `v0.5.0` asset/template comments change; assets stay
      `v0.11.0` and the skins verify plane is untouched.
- [x] `make gates`, `make ci-gates-parity` and the AGS unit tests pass; a
      temporary `dotfiles-v3` copy with `installer.pin: v0.1.36` passes
      `make deploy-coverage` while its program tuple names `v0.8.0`.
- [x] Engine `0.1.36` + CHANGELOG, annotated tag `v0.1.36` after the
      fast-forward merge; no push.

## Evidence / Verify

Branch `ticket/REQ-022-ags-platform-v08-mirror`, worktree
`.worktrees/REQ-022/`. Commits: `79253a9` (plan), `6d6a020`
(implementation + release metadata).

- Pin mirrors: `rg -n 'v0\.5\.0' ansible/roles/ags_platform
  ansible/roles/verify/vars/main.yml tests/fixtures/composition/dotfiles/provisioning/program-tuple.yaml`
  → no platform pin; the only remaining `v0.5.0` strings are asset/template
  history comments (`display_manager`, verify's desktop note) and host
  CHANGELOG/ticket history. `rg -n 'ags_platform_version:|verify_ags_platform_version:'
  ansible/roles` → both `v0.8.0`.
- Role derivation: `rg -n 'ags_platform_unit_dir|ags_platform_pin_file|shortcut'
  ansible/roles/ags_platform/vars/main.yml` → the unit dir is
  `{{ ags_platform_version }}`, the pin file is `<install>/ags-platform/pinned`,
  and no role-owned shortcut is declared. The verify mirror keeps the same
  three legs derived from `verify_ags_platform_version`.
- Targeted tests:
  `uv run --frozen pytest -q tests/unit/test_ags_platform_role.py
  tests/unit/test_ags_apps_units_role.py tests/unit/test_verify_role.py
  -m "not integration and not container_target"` → **163 passed,
  12 deselected in 356.33s**.
- `make gates` → **rc=0**:
  - `test`: `926 passed, 31 skipped, 52 deselected in 509.21s`
  - `lint`: `All checks passed!`
  - `hermetic`: `923 passed, 34 skipped, 52 deselected in 486.47s`
  - `lock-check`: `Resolved 33 packages in 0.63ms`
  - `docs-check`: rc=0
- `make ci-gates-parity` → **PASS**
  (`gates=['docs-check','hermetic','lint','lock-check','test']`,
  exempt `assets-parity, ci-gates-parity, release`).
- Composition proof without editing `dotfiles-v3` (temporary extracted copy of
  its `ticket/SKIN-PLANE-skin-plane-cutover` HEAD, whose tuple is already
  `v0.8.0`/`v0.6.0`/`v0.11.0`; engine cache pre-populated, offline):
  - Red with `installer.pin: v0.1.35`:
    `cd /tmp/opencode/req022-dcv/red && DOTFILES_PROVISION_OFFLINE=1 make deploy-coverage`
    → **rc=2**:
    `FAIL: dotfiles/provisioning/program-tuple.yaml: ags-platform 'v0.8.0' is
    not resolved by ansible/roles/ags_platform/vars/main.yml
    `ags_platform_version` = 'v0.5.0'`.
  - Green with `installer.pin: v0.1.36` and engine commit `6d6a020` cached as
    `.dev/dotfiles-provision-v0.1.36`:
    `cd /tmp/opencode/req022-dcv/green && DOTFILES_PROVISION_OFFLINE=1 make deploy-coverage`
    → **rc=0**:
    `CHECK pinned installer engine v0.1.36 ...` and
    `deploy-coverage: engine final topology — ags-platform v0.8.0 resolved by
    ags_platform and verify`.

## Handoff (dotfiles-v3)

- `dotfiles/provisioning/installer.pin`: `v0.1.36`
- `dotfiles/provisioning/program-tuple.yaml`: `ags-platform: v0.8.0`,
  `contracts: v0.6.0`, `dotfiles-assets: v0.11.0`

No `dotfiles-v3` file is edited by this ticket.
