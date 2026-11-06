---
id: REQ-024
title: "Mirror the dotfiles-v3 appearance v2 tuple in the engine"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-024/
branch: ticket/REQ-024-appearance-v2-mirrors
---

# Mirror the dotfiles-v3 appearance v2 tuple in the engine

## Requirement

Composition `dotfiles-v3` now declares the appearance-v2 program tuple:
`ags-platform: v0.9.0`, `contracts: v0.7.0` and `dotfiles-assets: v0.12.2`
(runtime is `v0.9.2` and is derived from `cli_tools_tags`, not mirrored here).
The engine still pinned platform `v0.8.0` and assets `v0.11.0`, and its skins
verify plane still described the frozen v1 manifests. A live v2 deploy would
therefore install v1 platform/assets, and `dotfiles-v3` `make deploy-coverage`
could not resolve the tuple.

## Acceptance

- [x] `ags_platform_version` and `verify_ags_platform_version` are `v0.9.0`
      and still derive unit dir/pin/shortcut from the one var.
- [x] Every `*_assets_pinned_tag` mirror (all nine role mirrors), the
      composition fixture `assets.yaml` (tag + checkout sources) and
      `program-tuple.yaml` (`ags-platform`/`contracts`/`dotfiles-assets`) are
      `v0.12.2`/`v0.9.0`/`v0.7.0`/`v0.12.2`.
- [x] The assets/verify `skins` schema support window is 2, so the v0.12.2
      `skins/schema.json` fetch passes.
- [x] Verify asserts v2 manifests (`schemaVersion = 2`, nested groups, optional
      mode overrides), the resolved `tokens.json` contract shape, all seven
      templates and v2 placeholder paths, and the contracts PIN `v0.7.0` with
      the appearance schema sha256 values.
- [x] v1-only checks are removed: no `schema_major = 1`, 24-token flat set or
      flat `hairline-w` requirement remains in the skins plane.
- [x] Runtime `skin.css`/`skin.json` pointer checks still tolerate absent
      pointers and reject a present non-`current/` pointer.
- [x] Tests/fixtures hardcoding `v0.8.0`/`v0.11.0` move to
      `v0.9.0`/`v0.12.2`; new tests prove a valid v2 plane passes and a
      tampered v2 manifest/template fails.
- [x] `make gates`, `make ci-gates-parity` and the local-corpus template-vars
      parity against `/home/inumaki/Development/dotfiles/dotfiles-assets` pass.
- [x] Engine `0.1.38` + CHANGELOG; annotated tag `v0.1.38` after the
      fast-forward merge; push `main` and the tag; no apply.

## Evidence / Verify

Branch `ticket/REQ-024-appearance-v2-mirrors`, worktree
`.worktrees/REQ-024/`. Commits: `13ccfff` (plan), `ec56b05`
(implementation + release metadata), plus this evidence commit.

- Platform pin mirror: `rg -n 'ags_platform_version:|verify_ags_platform_version:'
  ansible/roles` → both `v0.9.0`; the unit dir, pin file and shared shortcut
  still derive from `ags_platform_version`.
- Assets pin mirrors: `rg -n 'assets_pinned_tag:'
  ansible/roles/*/vars/main.yml` → all nine mirrors are `v0.12.2`
  (`assets`, `btop_config`, `compositor_configs`, `config_copies`,
  `display_manager`, `kitty_config`, `verify`, `wlogout_config`,
  `zsh_config`). No `v0.11.0` or `v0.8.0` remains under `ansible/` or
  `tests/` (historical `v0.6.0` SDDM comments are unrelated asset history).
- Composition fixture: `tests/fixtures/composition/dotfiles/provisioning/
  program-tuple.yaml` → `ags-platform: v0.9.0`, `contracts: v0.7.0`,
  `dotfiles-assets: v0.12.2`; `assets.yaml` tag and all four checkout sources
  are `v0.12.2`.
- Schema window: `ansible/roles/assets/vars/main.yml` and
  `ansible/roles/verify/vars/main.yml` both carry `skins: 2`; the v0.12.2
  `skins/schema.json` declares `schema_major: 2`.
- V2 verify: `ansible/roles/verify/vars/main.yml` carries the 57 nested CSS
  token paths, the five manifest groups, the `v0.7.0` contract PIN and the
  `appearance-manifest/json/artifact` + frozen v1 contract set. The tasks
  validate each manifest with `tomllib` (nested token paths and optional
  `mode.dark`/`mode.light`), compare template placeholders to the v2 path
  vocabulary, assert the resolved `tokens.json` contract is
  `{version: 2, surface, state, type, ink, layout}`, and re-hash every
  vendored contract against `contracts/PIN`.
- Corpus matches the PIN: local `dotfiles-assets` checkout is exactly
  `v0.12.2`; `skins/contracts/PIN` records `contracts=v0.7.0` and six
  sha256 lines; seven `skins/templates/<configDir>.gtk.css.j2` files exist.
- Targeted tests:
  - `uv run pytest -q tests/unit/test_verify_role.py::TestVerifyVars` →
    **44 passed**
  - `uv run pytest -q tests/unit/test_verify_role.py::TestVerifySkinPlane` →
    **5 passed** (valid v2 plane; missing template; v1/tampered v2 manifest;
    unknown/layout template placeholder; tampered contract)
  - `uv run pytest -q tests/unit/test_verify_role.py::TestVerifyAssetsSchemaWindow`
    → **7 passed**
  - `uv run pytest -q tests/unit/test_assets_role.py` → **38 passed**
  - `uv run pytest -q tests/unit/test_ags_platform_role.py
    tests/unit/test_ags_apps_units_role.py` → **55 passed**
- Local-corpus template-vars parity:
  `DOTFILES_ASSETS_REPO=/home/inumaki/Development/dotfiles/dotfiles-assets
  DOTFILES_ASSETS_TEMPLATES_DIR=.../templates uv run pytest -q
  tests/unit/test_template_vars_parity.py` → **10 passed**.
- `make gates` → **rc=0**:
  - `test`: `944 passed, 31 skipped, 52 deselected in 615.11s`
  - `lint`: `All checks passed!`
  - `hermetic`: `941 passed, 34 skipped, 52 deselected in 569.83s`
  - `lock-check`: `Resolved 33 packages in 0.62ms`
  - `docs-check`: rc=0
- `make ci-gates-parity` → **PASS**:
  `gates=['docs-check','hermetic','lint','lock-check','test']`,
  CI jobs add only `assets-parity, ci-gates-parity, release`.
- Release: engine `0.1.38` in `pyproject.toml`, `src/provisioning/__init__.py`
  and `uv.lock`; annotated tag `v0.1.38` created on the fast-forward merge
  commit. `main` and the tag pushed. No `make apply` was run.

## Handoff (dotfiles-v3)

Exact values for the composition:

- `dotfiles/provisioning/installer.pin`: `v0.1.38`
- `dotfiles/provisioning/program-tuple.yaml`: `ags-platform: v0.9.0`,
  `contracts: v0.7.0`, `dotfiles-assets: v0.12.2`
- `dotfiles/provisioning/assets.yaml`: `assets.tag: v0.12.2` and all four
  checkout sources under `assets/v0.12.2/`

No `dotfiles-v3` file is edited by this ticket.
