---
id: REQ-030
title: "Mirror the final v3 composition: ags-platform v1.0.0 and v3 app tags"
kind: requirement
status: done
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

- [x] `ansible/roles/ags_platform/vars/main.yml` pins
      `ags_platform_version: v1.0.0`; the unit dir, pin file and shared
      shortcut still derive from that one var.
- [x] `ansible/roles/verify/vars/main.yml` mirrors
      `verify_ags_platform_version: v1.0.0`; unit dir/pin/shortcut remain
      derived, with no stale literal.
- [x] Composition fixture `program-tuple.yaml` reads
      `ags-platform: v1.0.0`, keeps `contracts: v0.8.0` and
      `dotfiles-assets: v0.13.0`.
- [x] `tests/fixtures/ags-apps/app-list/all-standalone.apps.yaml` and
      `tests/fixtures/composition/dotfiles/provisioning/apps.yaml` pin the
      seven v3 tags above (repos stay fixture placeholders).
- [x] Unit tests that stand in for a host (`test_ags_platform_role.py`,
      `test_ags_apps_units_role.py`, `test_verify_role.py`) use `v1.0.0` and
      the v3 app inventory; no stale `v0.9.1` or v2 app-tag literal remains.
- [x] Contracts remain `v0.8.0`, generation verify remains `version: 3`, and
      the v0.1.43 locality tests pass unchanged.
- [x] Targeted AGS/verify tests, `make gates` and `make ci-gates-parity` pass.
- [x] Engine `0.1.44` + CHANGELOG, annotated tag `v0.1.44` after the
      fast-forward merge; push `main` and the tag; no apply.

## Non-goals

- No `dotfiles-v3` file, runtime pin, assets pin, contract tag or live host is
  changed here.
- No v3 locality behaviour, generation schema or verify gate is relaxed.

## Evidence / Verify

Worktree `.worktrees/REQ-030/`, branch
`ticket/REQ-030-v3-final-mirrors`. Commits: `ff07ae4` (plan), `609381f`
(implementation + release metadata), plus this evidence commit. Annotated tag
`v0.1.44` created on the fast-forward merge commit; no apply was run.

- Upstream releases exist in the local app checkouts
  (`git -C ../<repo> tag --sort=-v:refname | head -1`):
  bar `v0.6.0`, notifications `v0.5.0`, capture `v0.7.0`, clipboard `v0.6.0`,
  wallpaper-selector `v0.5.0`, icme `v0.5.0`, btop-theme-studio `v0.5.0`,
  ags-platform `v1.0.0`.
- Pin mirrors:
  `rg -n 'ags_platform_version:|verify_ags_platform_version:'
  ansible/roles/ags_platform/vars/main.yml ansible/roles/verify/vars/main.yml`
  → role `v1.0.0`, verify `v1.0.0`. The unit dir is
  `{{ ags_platform_install_root }}/{{ ags_platform_version }}`, the pin file is
  `<install>/ags-platform/pinned`, and the shared shortcut is owned by
  `ags_apps_units`; no path literal changed.
- Composition fixture tuple:
  `rg -n 'ags-platform:|contracts:|dotfiles-assets:'
  tests/fixtures/composition/dotfiles/provisioning/program-tuple.yaml`
  → `ags-platform: v1.0.0`, `contracts: v0.8.0`,
  `dotfiles-assets: v0.13.0`.
- Final app inventory (one command, both final-topology files):

  ```
  python3 - <<'PY'
  import yaml
  from pathlib import Path
  for rel in ("tests/fixtures/ags-apps/app-list/all-standalone.apps.yaml",
              "tests/fixtures/composition/dotfiles/provisioning/apps.yaml"):
      apps = yaml.safe_load(Path(rel).read_text())["apps"]
      print(rel, {entry["app"]: entry["tag"] for entry in apps})
  PY
  ```

  → both files print `{'bar': 'v0.6.0', 'notifications': 'v0.5.0',
  'capture': 'v0.7.0', 'clipboard': 'v0.6.0', 'wallpaper-selector':
  'v0.5.0', 'icme': 'v0.5.0', 'btop-theme-studio': 'v0.5.0'}`.
- Generations v3 is retained:
  `rg -n 'verify_generation_contract_tag:|verify_generation_manifest_version:'
  ansible/roles/verify/vars/main.yml` → `verify_generation_manifest_version: 3`,
  `verify_generation_contract_tag: v0.8.0`. The v0.1.43 locality suite
  (`tests/unit/test_v3_locality.py`) passes unchanged.
- Stale-literal sweep:
  `rg -n 'v0\.9\.1' --glob '!CHANGELOG.md' --glob '!tickets/**' .` → no
  matches (historical CHANGELOG/ticket records are untouched).
- Targeted AGS/verify suites:
  `uv run --frozen pytest -q tests/unit/test_ags_platform_role.py
  tests/unit/test_ags_apps_units_role.py tests/unit/test_ags_units_supervision.py
  tests/unit/test_verify_role.py tests/unit/test_v3_locality.py
  -m "not integration and not container_target"` → **205 passed,
  15 deselected in 786.47s**.
- `make gates` → **rc=0**:
  - `test`: `996 passed, 3 skipped, 55 deselected in 965.84s`
  - `lint`: `All checks passed!`
  - `hermetic`: `965 passed, 34 skipped, 55 deselected in 900.46s`
  - `lock-check`: `Resolved 33 packages in 0.70ms`
  - `docs-check`: rc=0
- `make ci-gates-parity` → **rc=0**:
  `PASS gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test']`;
  CI-only exempt `assets-parity, ci-gates-parity, release`.
- Optional composition proof: the local `dotfiles-v3` checkout is still
  **pre-v3** (`FINAL_APP_RELEASES` v0.4.x/v0.5.0/v0.6.1, tuple contracts
  `v0.7.0`). A temp copy at `/tmp/opencode/req030-dcv/` with
  `installer.pin: v0.1.44`, tuple `ags-platform: v1.0.0`/`contracts: v0.8.0`
  and the v3 app tags reached the pinned engine (`CHECK pinned installer engine
  v0.1.44`) but its own stale gate then failed with
  `missing 'barPalettePointer' — the standalone verify mirror is incomplete`;
  that guard predates the v0.1.43 immutable-tag locality, not the new pins.
  `dotfiles-v3` itself was not edited.

## Handoff (dotfiles-v3)

- `dotfiles/provisioning/installer.pin`: `v0.1.44`
- `dotfiles/provisioning/program-tuple.yaml`:
  `ags-platform: v1.0.0`, `contracts: v0.8.0`, `dotfiles-assets: v0.13.0`
- `dotfiles/provisioning/apps.yaml` and `scripts/ags_app_consumption.py`
  `FINAL_APP_RELEASES`: bar `v0.6.0`, notifications `v0.5.0`, capture
  `v0.7.0`, clipboard `v0.6.0`, wallpaper-selector/icme/btop-theme-studio
  `v0.5.0`; the v3 deploy-coverage guard must drop the retired
  `barPalettePointer` assertion.

No `dotfiles-v3` file is edited by this ticket.

