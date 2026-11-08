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

- [x] `ansible/roles/ags_platform/vars/main.yml`: `ags_platform_version` is
      `v1.0.1`; the unit dir, pin file and shared shortcut still derive from
      that one var.
- [x] `ansible/roles/verify/vars/main.yml`: `verify_ags_platform_version` is
      `v1.0.1`; unit dir/pin/shortcut remain derived, with no stale literal.
- [x] Composition fixture `program-tuple.yaml`: `ags-platform: v1.0.1`,
      `contracts: v0.8.0`, `dotfiles-assets: v0.13.0`.
- [x] Unit tests that stand in for a host (`test_ags_platform_role.py`,
      `test_ags_apps_units_role.py`, `test_verify_role.py`) use `v1.0.1`; no
      hardcoded `v1.0.0` platform fixture/simulation literal remains.
- [x] Contracts remain `v0.8.0`, generation verify remains `version: 3`, and
      the v3 generation/locality tests pass unchanged.
- [x] Targeted AGS/verify tests, `make gates` and `make ci-gates-parity` pass.
- [x] Engine `0.1.48` + CHANGELOG, annotated tag `v0.1.48` after the
      fast-forward merge; push `main` and the tag; GitHub Release carries only
      the 0.1.48 sdist and wheel; no apply.

## Non-goals

- No `dotfiles-v3` file, runtime pin, assets pin, contract tag or live host is
  changed here.
- No v3 locality behaviour, generation schema or verify gate is relaxed.

## Evidence / Verify

Worktree `.worktrees/REQ-031/`, branch
`ticket/REQ-031-platform-v101-mirror`. Commits: `3a0098a` (plan), `87cb2b8`
(implementation + release metadata), plus this evidence commit. Annotated tag
`v0.1.48` created on the fast-forward merge commit; no apply was run.

- Upstream patch exists: `git -C ../ags-platform show -s --format='%H %s'
  v1.0.1` → `10b4d11cc4cc38cb68ebda7a849023206ad8b801
  docs(BUG-002): record appearance CSS hex validation evidence`, tag message
  `ags-platform v1.0.1 — appearance CSS hex literal validation (BUG-002)`.
- Pin mirrors:
  `rg -n 'ags_platform_version:|verify_ags_platform_version:'
  ansible/roles/ags_platform/vars/main.yml ansible/roles/verify/vars/main.yml`
  → role `v1.0.1`, verify `v1.0.1`. The unit dir is
  `{{ ags_platform_install_root }}/{{ ags_platform_version }}`, the pin file is
  `<install>/ags-platform/pinned`, and the shared shortcut is owned by
  `ags_apps_units`; no path literal changed.
- Composition fixture tuple:
  `rg -n 'ags-platform:|contracts:|dotfiles-assets:'
  tests/fixtures/composition/dotfiles/provisioning/program-tuple.yaml`
  → `ags-platform: v1.0.1`, `contracts: v0.8.0`,
  `dotfiles-assets: v0.13.0`.
- v3 app tags unchanged: the final all-standalone app-list fixture and the
  composition `apps.yaml` still print `{'bar': 'v0.6.0', 'notifications':
  'v0.5.0', 'capture': 'v0.7.0', 'clipboard': 'v0.6.0',
  'wallpaper-selector': 'v0.5.0', 'icme': 'v0.5.0',
  'btop-theme-studio': 'v0.5.0'}` (REQ-030 inventory command).
- Generations v3 retained:
  `rg -n 'verify_generation_contract_tag:|verify_generation_manifest_version:'
  ansible/roles/verify/vars/main.yml` → `verify_generation_manifest_version: 3`,
  `verify_generation_contract_tag: v0.8.0`. `tests/unit/test_v3_locality.py`
  passes unchanged.
- Stale platform-literal sweep:
  `rg -n 'v1\.0\.0' --glob '!CHANGELOG.md' --glob '!tickets/**' .
  --glob '!dist/**' --glob '!*.lock'` → only the four unrelated generic
  `tag: v1.0.0` CLI-validation fixtures in `test_cli_tools_role.py`; no
  platform pin/fixture literal remains.
- Targeted AGS/verify/locality suites:
  `uv run --frozen pytest -q tests/unit/test_ags_platform_role.py
  tests/unit/test_ags_apps_units_role.py
  tests/unit/test_ags_units_supervision.py tests/unit/test_verify_role.py
  tests/unit/test_v3_locality.py -m "not integration and not container_target"`
  → **214 passed, 18 deselected in 975.16s** (rc=0).
- `make gates` → **rc=0**:
  - `test`: `1005 passed, 3 skipped, 60 deselected in 1166.58s`
  - `lint`: `All checks passed!`
  - `hermetic`: `974 passed, 34 skipped, 60 deselected in 1083.74s`
  - `lock-check`: `Resolved 33 packages in 0.65ms`
  - `docs-check`: rc=0
- `make ci-gates-parity` → **rc=0**:
  `PASS gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test']`;
  CI-only exempt `assets-parity, ci-gates-parity, release`.

## Handoff (dotfiles-v3)

- `dotfiles/provisioning/installer.pin`: `v0.1.48`
- `dotfiles/provisioning/program-tuple.yaml`:
  `ags-platform: v1.0.1`, `contracts: v0.8.0`, `dotfiles-assets: v0.13.0`

No `dotfiles-v3` file is edited by this ticket.
