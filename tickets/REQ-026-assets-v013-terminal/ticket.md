---
id: REQ-026
title: "Consume dotfiles-assets v0.13.0 (terminal skin, cleanup layout removal)"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-026/
branch: ticket/REQ-026-assets-v013-terminal
---

# Consume dotfiles-assets v0.13.0

## Requirement

`dotfiles-assets` v0.13.0 adds the fourth Appearance v2 built-in skin
`terminal` (dense monospace, square/hairline; panel radius 0) and removes the
CSS-min-derived `[groups.layout.ags-capture]` and
`[groups.layout.ags-btop-studio]` blocks from every manifest. The engine pinned
v0.12.2 and its skin plane accepted only glass/flat/paper, so a v0.13.0 deploy
would fail verify on the fourth manifest and the retired layout groups.

The engine must mirror the assets tag across all nine `*_assets_pinned_tag`
mirrors and the composition fixture, accept and expand the four v2 manifests
(glass/flat/paper/terminal) through all seven templates, keep the v2
schema/nested-group/appearance-json/contracts PIN v0.7.0 checks, and assert the
retired capture/btop layout blocks are absent without requiring optional layout
groups.

## Acceptance

- [x] Every `*_assets_pinned_tag` mirror (all nine roles), the composition
      fixture `assets.yaml` (tag + four checkout sources) and
      `program-tuple.yaml` `dotfiles-assets` are `v0.13.0`.
- [x] The skins verify plane accepts four manifests (`glass`, `flat`, `paper`,
      `terminal`) and expands all seven `*.gtk.css.j2` templates for every
      manifest × mode.
- [x] Verify retains the v2 checks: `schemaVersion = 2`, name matching the
      file, nested `groups.surface/state/type/ink/layout`, optional mode
      overrides, the resolved `tokens.json` appearance-json contract and the
      vendored contracts PIN `v0.7.0` with sha256 values.
- [x] The `terminal` manifest's dense values are checked structurally
      (`surface.panel.radius = 0`, `type.font-family` contains `monospace`).
- [x] `[groups.layout.ags-capture]` and `[groups.layout.ags-btop-studio]` are
      absent from every deployed manifest; missing optional layout groups are
      not failures.
- [x] Hardcoded `v0.12.2` fixtures/tests move to `v0.13.0`; a terminal-skin
      verify test proves a valid terminal manifest passes and a tampered
      terminal manifest fails.
- [x] `make gates`, `make ci-gates-parity` and local-corpus assets parity
      against `/home/inumaki/Development/dotfiles/dotfiles-assets` pass.
- [x] Engine `0.1.40` + CHANGELOG; annotated tag `v0.1.40` after the
      fast-forward merge; push `main` and the tag; no apply.

## Evidence / Verify

Branch `ticket/REQ-026-assets-v013-terminal`, worktree
`.worktrees/REQ-026/`. Commits: `38fe5b7` (plan), `9ae459d`
(implementation + release metadata), plus this evidence commit.

- Pin mirrors: `rg -n 'assets_pinned_tag:' ansible/roles/*/vars/main.yml`
  → all nine mirrors are `v0.13.0` (`assets`, `btop_config`,
  `compositor_configs`, `config_copies`, `display_manager`, `kitty_config`,
  `verify`, `wlogout_config`, `zsh_config`).
- Composition fixture: `tests/fixtures/composition/dotfiles/provisioning/
  program-tuple.yaml` → `dotfiles-assets: v0.13.0` (platform `v0.9.0` and
  contracts `v0.7.0` unchanged); `assets.yaml` `assets.tag` and all four
  checkout sources are `v0.13.0`.
- No live `v0.12.2` remains: `rg -n 'v0\.12\.2' . --hidden --glob
  '!.git/**' --glob '!.worktrees/**' --glob '!tickets/**'
  --glob '!CHANGELOG.md'` → no matches. The remaining text is historical
  ticket/CHANGELOG prose.
- Corpus: local `dotfiles-assets` checkout is exactly tag `v0.13.0`
  (`git describe --tags --exact-match HEAD`), with four manifests
  (`glass`, `flat`, `paper`, `terminal`), seven
  `skins/templates/<configDir>.gtk.css.j2` files, and
  `skins/contracts/PIN` still at `contracts=v0.7.0` with six sha256 lines.
  `terminal.toml` carries `surface.panel.radius = 0` and
  `type.font-family = "JetBrainsMono Nerd Font, monospace"`.
- Verify plane: `verify_skins_manifest_names` is the four manifests. The
  manifest check keeps `schemaVersion = 2`, name/file agreement, the five
  nested groups, optional mode overrides and all 57 CSS token paths; it adds
  the terminal dense-value assertions and rejects the retired
  `layout.ags-capture`/`layout.ags-btop-studio` blocks (optional layout groups
  are never required). A new task expands all seven templates through every
  manifest × mode (4 × 2 = 8 resolutions) and fails on an unresolved or
  leftover placeholder. The appearance-json contract and contracts PIN
  `v0.7.0` sha256 checks are unchanged.
- Real-corpus skin probe (materialized `<spine>/skins` from the local
  `dotfiles-assets` v0.13.0 checkout through the real role tasks):
  `ansible-playbook` → **ok=17 changed=0 failed=0**.
- Targeted tests:
  - `pytest -q tests/unit/test_verify_role.py::TestVerifyVars` → **44 passed**
  - `pytest -q tests/unit/test_verify_role.py::TestVerifySkinPlane` →
    **8 passed** (four-manifest valid plane + explicit terminal pass;
    missing template; tampered v2/template/terminal/retired-layout/contract).
  - `pytest -q tests/unit/test_display_manager_role.py::TestSddmVars
    tests/unit/adapters/test_yaml_manifest_reader.py
    tests/unit/test_assets_role.py tests/unit/test_ags_apps_units_role.py`
    combined with the verify skin suites → **208 passed**.
- Local-corpus assets parity:
  `DOTFILES_ASSETS_REPO=/home/inumaki/Development/dotfiles/dotfiles-assets
  DOTFILES_ASSETS_TEMPLATES_DIR=.../templates pytest -q
  tests/unit/test_template_vars_parity.py` → **10 passed**.
- `make gates` → **rc=0**:
  - `test`: `951 passed, 31 skipped, 55 deselected in 726.56s`
  - `lint`: `All checks passed!`
  - `hermetic`: `948 passed, 34 skipped, 55 deselected in 696.31s`
  - `lock-check`: `Resolved 33 packages in 0.71ms`
  - `docs-check`: rc=0
- `make ci-gates-parity` → **PASS**:
  `gates=['docs-check','hermetic','lint','lock-check','test']`, CI jobs add
  only `assets-parity, ci-gates-parity, release`.
- Release: engine `0.1.40` in `pyproject.toml`, `src/provisioning/__init__.py`
  and `uv.lock`; annotated tag `v0.1.40` created on the fast-forward merge
  commit. `main` and the tag pushed. No `make apply` was run.

## Handoff (dotfiles-v3)

Exact values for the composition:

- `dotfiles/provisioning/installer.pin`: `v0.1.40`
- `dotfiles/provisioning/program-tuple.yaml`: `dotfiles-assets: v0.13.0`
  (platform `v0.9.0`, contracts `v0.7.0` unchanged)
- `dotfiles/provisioning/assets.yaml`: `assets.tag: v0.13.0` and all four
  checkout sources under `assets/v0.13.0/`

No `dotfiles-v3` file is edited by this ticket.
