---
id: REQ-027
title: "Pin the final seven-app AGS release tags in the engine fixtures"
kind: requirement
status: done
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

- [x] `tests/fixtures/ags-apps/app-list/all-standalone.apps.yaml` and
      `tests/fixtures/composition/dotfiles/provisioning/apps.yaml` pin the
      seven final tags above (repos stay fixture placeholders).
- [x] `test_ags_apps_units_role.py` execution helpers create each fake app
      repo at its fixture tag and assert installs/pins/tag bumps against
      `entry["tag"]`; no stale `v0.1.0` topology assumption remains.
- [x] `test_verify_role.py`'s provisioned-layout simulation builds every AGS
      unit from the fixture tag;
      `TestAllStandaloneFixture::test_fixture_pins_the_final_released_tags`
      asserts the final seven-app inventory tags are exactly the table above.
- [x] Targeted AGS/verify tests, `make gates` and `make ci-gates-parity` pass.
- [x] Engine `0.1.41` + CHANGELOG; annotated tag `v0.1.41` after the
      fast-forward merge; push `main` and the tag; no apply.

## Evidence / Verify

Worktree `.worktrees/REQ-027/`, branch
`ticket/REQ-027-final-app-tags`. Commits: `4c21cfd` (plan), `f9bd255`
(implementation + release metadata), plus this evidence commit.

- Fixture inventory (one command, both final-topology files):

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

  → both files print `{'bar': 'v0.5.0', 'notifications': 'v0.4.0',
  'capture': 'v0.6.1', 'clipboard': 'v0.5.0', 'wallpaper-selector':
  'v0.4.1', 'icme': 'v0.4.1', 'btop-theme-studio': 'v0.4.1'}`.
- The fixture tags are the released tags of the local app checkouts:
  `git -C ../ags-capture-tool tag --sort=-v:refname | head -1` → `v0.6.1`;
  the same first-line query gives `v0.5.0` (bar), `v0.4.0` (notifications),
  `v0.5.0` (clipboard), `v0.4.1` (wallpaper-selector, icme,
  btop-theme-studio).
- `uv run pytest -q tests/unit/test_ags_apps_units_role.py
  ::TestAllStandaloneFixture -m "not integration and not container_target"`
  → **7 passed in 0.05s** (includes the new final-tag inventory test).
- Targeted AGS/verify suites:
  `uv run pytest -q tests/unit/test_ags_apps_units_role.py
  tests/unit/test_ags_units_supervision.py tests/unit/test_verify_role.py
  -m "not integration and not container_target"` → **173 passed,
  15 deselected in 566.41s**. The `ags_apps_units` execution tests now create
  each fake repo at `entry["tag"]` (bar v0.5.0 … btop v0.4.1) and pass.
- Verify-role topology proof:
  `uv run pytest -q "tests/unit/test_verify_role.py::TestVerifyRuntime
  ::test_verify_passes_on_a_provisioned_machine" -m integration` →
  **1 passed in 153.68s**. `_build_provisioned_layout` creates every
  `<install>/apps/<installDir>/<tag>` unit and `pinned` record from the
  fixture entry, so the replay installs/verifies the final inventory.
- `make gates` → **rc=0**:
  - `test`: `952 passed, 31 skipped, 55 deselected in 700.36s`
  - `lint`: `All checks passed!`
  - `hermetic`: `949 passed, 34 skipped, 55 deselected in 668.65s`
  - `lock-check`: `Resolved 33 packages in 0.83ms`
  - `docs-check`: rc=0
- `make ci-gates-parity` → **PASS**:
  `gates=['docs-check','hermetic','lint','lock-check','test']`; CI-only
  exempt `assets-parity, ci-gates-parity, release`.
- Release: engine `0.1.41` in `pyproject.toml`,
  `src/provisioning/__init__.py` and `uv.lock`; annotated tag `v0.1.41`
  created on the fast-forward merge commit. `main` and the tag pushed. No
  `make apply` was run.

## Handoff (dotfiles-v3)

The direct `deploy-coverage` assertion that named
`capture … not the final released tag 'v0.6.0'` is the composition's own
`FINAL_APP_RELEASES` map in `scripts/ags_app_consumption.py`. This repo does
not edit `dotfiles-v3`; that map must move to capture `v0.6.1`, clipboard
`v0.5.0` and btop-theme-studio `v0.4.1` (bar/notifications/wallpaper-selector/
icme unchanged). The engine side now agrees with that final inventory.
- Bump `dotfiles/provisioning/installer.pin` to `v0.1.41` in the next wave.
- No `dotfiles-assets` change is needed.
