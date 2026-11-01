---
id: REQ-017
title: "Bump ags-platform pin to v0.4.0 (theme-provider Phase A)"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-017/
branch: ticket/REQ-017-ags-platform-v040
---

# Bump ags-platform pin to v0.4.0

## Requirement

ags-platform `v0.4.0` ships theme-provider Phase A: the typed `palette()` role
API plus one subscription. Legacy `@color_*` CSS behavior is byte-identical, so
this is a mechanical pin bump with no app-code or role-behavior change.

The platform tag is mirrored in three places — the `ags_platform` role vars, the
`verify` role vars, and the composition `program-tuple.yaml` fixture — plus the
unit tests that assert the tag. Move all platform mirrors to `v0.4.0`; leave
`contracts` and `dotfiles-assets` untouched.

## Acceptance

- [x] `ansible/roles/ags_platform/vars/main.yml`: `ags_platform_version` is
      `v0.4.0`.
- [x] `ansible/roles/verify/vars/main.yml`: `verify_ags_platform_version` is
      `v0.4.0`.
- [x] `tests/fixtures/composition/dotfiles/provisioning/program-tuple.yaml`:
      `ags-platform: v0.4.0`; `contracts` stays `v0.3.0`.
- [x] Unit-test expectations for the platform tag move to `v0.4.0`
      (`test_ags_platform_role`, `test_ags_apps_units_role`,
      `test_verify_role`); contracts/assets expectations are unchanged.
- [x] `rg -n 'ags.platform' ansible tests/fixtures tests/unit --glob
      '*.{yml,yaml,py}'` shows only `v0.4.0` for the platform.
- [x] `rg -n 'v0\.3\.0' ansible tests/fixtures --glob '*.{yml,yaml}'` leaves
      only contracts/assets/history references.
- [x] `make gates` and `make ci-gates-parity` pass; version `0.1.31` plus
      CHANGELOG entry. No tag/push/merge.

## Known debt (follow-up, not this ticket)

The platform pin is still mirrored (role + verify + program tuple) instead of
being derived from the program tuple. `ags_apps_units` already reads
`ags_apps_units_tuple['ags-platform']`, and its task asserts the role tag and
tuple tag agree, but the role and verify still carry separate literals. Deriving
both mirrors from `program-tuple.yaml` (like `cli_tools_tags`) is a follow-up;
this ticket stays a mechanical bump.

## Evidence / Verify

- Branch: `ticket/REQ-017-ags-platform-v040`; worktree `.worktrees/REQ-017/`.
- `rg -n 'ags.platform' ansible tests/fixtures tests/unit --glob
  '*.{yml,yaml,py}'`: only `v0.4.0` for `ags-platform`.
- `rg -n 'v0\.3\.0' ansible tests/fixtures --glob '*.{yml,yaml}'` (exact):
  ```
  tests/fixtures/composition/dotfiles/provisioning/program-tuple.yaml:6:# cutover. The contracts repo owns the schema (v0.3.0,
  tests/fixtures/composition/dotfiles/provisioning/program-tuple.yaml:11:contracts: v0.3.0
  tests/fixtures/composition/dotfiles/provisioning/config-copies.yaml:8:# S2 (assets v0.3.0): the static corpus ships in the `dotfiles-assets` repo
  tests/fixtures/composition/dotfiles/provisioning/apps.yaml:9:# The contracts repo owns the schema (v0.3.0,
  ansible/roles/config_copies/vars/main.yml:11:# S2 (assets v0.3.0): the corpus is the PINNED `dotfiles-assets` repo, `configs/`
  ```
  Justification: the two `contracts` lines are the intentionally unchanged
  schema/tuple tag; the other three are historical comments naming the
  assets corpus at its old `v0.3.0` tag, not live pins.
- `make gates` → **PASS**: `test` 945 passed, 3 skipped, 52 deselected
  (23m44s); `lint` → `All checks passed!`; `hermetic` 914 passed, 34 skipped,
  52 deselected (20m31s); `lock-check` → `Resolved 33 packages in 1ms`;
  `docs-check` → rc=0.
- `make ci-gates-parity` → **PASS**:
  `gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test']`,
  `jobs=['assets-parity', 'ci-gates-parity', 'docs-check', 'hermetic', 'lint',
  'lock-check', 'release', 'test']`, `exempt=['assets-parity',
  'ci-gates-parity', 'release']`.
- Targeted affected suites: `146 passed, 12 skipped, 12 deselected`.

## Outcome

Pending. Status stays `in-progress`; no tag/push/merge.
