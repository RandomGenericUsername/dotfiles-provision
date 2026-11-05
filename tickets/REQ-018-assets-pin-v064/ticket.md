---
id: REQ-018
title: "Consume dotfiles-assets v0.6.4 (rofi/wlogout on semantic roles)"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-018/
branch: ticket/REQ-018-assets-pin-v064
---

# Consume dotfiles-assets v0.6.4

## Requirement

assets v0.6.4 migrates `configs/rofi/launcher/config.rasi` and
`templates/wlogout/style.css.tpl` from CSG carrier tokens to `palette.v1`
roles. Rofi's window/field previously used `@color01` = Material **error**
(invariant in every palette), so it never changed color with the wallpaper.
Every corpus pin mirror in the engine and the composition moves to v0.6.4.

## Acceptance

- [x] All `*_assets_pinned_tag` mirrors = v0.6.4 (assets, verify, btop,
      compositor, config_copies, display, kitty, wlogout, zsh).
- [x] Fixture manifests (assets sources, program tuple) = v0.6.4.
- [x] Tests updated; `make gates` green; engine version `0.1.32` plus
      CHANGELOG entry.
- [x] Live bootstrap deploys the rofi config; rofi follows the wallpaper.

## Known debt (follow-up, not this ticket)

The corpus pin is still mirrored in nine roles and repeated in
`tests/fixtures/composition/dotfiles/provisioning/assets.yaml`. Single-sourcing
the pin from `assets.yaml` (like `cli_tools_tags`, REQ-014) would remove the
nine literal mirrors and the parity guard that keeps them in step; tracked
separately so this pin bump stays mechanical.

## Evidence / Verify

- Branch: `ticket/REQ-018-assets-pin-v064`; worktree `.worktrees/REQ-018/`.
- Pin commit: `fb5b146` — `REQ-018: consume dotfiles-assets v0.6.4; release
  0.1.32` (version `0.1.31` → `0.1.32` in `pyproject.toml`,
  `src/provisioning/__init__.py` and `uv.lock`).
- `rg -n 'v0\.6\.3' ansible tests --glob '*.{yml,yaml,py}'` → **no matches**
  (exit 1). The only old-tag references left in the repo are historical
  CHANGELOG/REQ-015 ticket text.
- Intentional `v0.6.2` autostart fixture references kept (its content is
  unchanged in v0.6.4): `tests/fixtures/ags-apps/autostart/v0.6.2.lua` and the
  two test references to it.
- `make gates` → **PASS** (overall rc=0):
  - `test`: `917 passed, 31 skipped, 52 deselected in 1178.66s (0:19:38)`
  - `lint`: `All checks passed!`
  - `hermetic`: `914 passed, 34 skipped, 52 deselected in 738.37s (0:12:18)`
  - `lock-check`: `Resolved 33 packages in 0.76ms`
  - `docs-check`: rc=0
- `make ci-gates-parity` → **PASS**:
  `gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test']`,
  `jobs=['assets-parity', 'ci-gates-parity', 'docs-check', 'hermetic',
  'lint', 'lock-check', 'release', 'test']`,
  `exempt=['assets-parity', 'ci-gates-parity', 'release']`.
- Corpus-backed target (local `dotfiles-assets` checkout at `v0.6.4`):
  `DOTFILES_ASSETS_REPO=... DOTFILES_ASSETS_TEMPLATES_DIR=... uv run pytest -q
  tests/unit/test_wlogout_config_role.py tests/unit/test_template_vars_parity.py`
  → `25 passed in 2.78s`. The wlogout template now asserts `@on_surface` /
  `@primary_container`, and the verify wiring gate greps those roles (no
  `@color_1x`).
- `uv run pytest -q -m integration
  tests/unit/test_verify_role.py::TestVerifyRuntime` → `12 passed in 547.10s
  (0:09:07)` (the real verify playbook passes with the updated wlogout gate).

## Outcome

Released engine `v0.1.32`, deployed via PIN-0130 on 2026-11-04 (verify green,
291 tasks). Live proof:
- assets pin `v0.6.4`; deployed rofi config has zero carrier tokens and uses
  `@surface-container`/`@surface-container-high`/`@primary`/`@primary-container`;
- `rofi -dump-theme` resolves role values that change with the wallpaper:
  default `primary rgba(185,195,255)` / `surface-container rgba(31,31,37)` →
  eagle `rgba(255,181,154)` / `rgba(39,29,26)` → restored back;
- bar refresh in the same cycle: `status: applied`, `mode: restart`.
