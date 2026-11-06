---
id: REQ-026
title: "Consume dotfiles-assets v0.13.0 (terminal skin, cleanup layout removal)"
kind: requirement
status: in-progress
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
`[groups.layout.ags-btop-studio]` blocks from every manifest. The engine still
pins v0.12.2 and its skin plane accepts only glass/flat/paper, so a v0.13.0
deploy would fail verify on the fourth manifest and the retired layout groups.

The engine must mirror the assets tag across all nine `*_assets_pinned_tag`
mirrors and the composition fixture, accept and expand the four v2 manifests
(glass/flat/paper/terminal) through all seven templates, keep the v2
schema/nested-group/appearance-json/contracts PIN v0.7.0 checks, and assert the
retired capture/btop layout blocks are absent without requiring optional layout
groups.

## Acceptance

- [ ] Every `*_assets_pinned_tag` mirror (all nine roles), the composition
      fixture `assets.yaml` (tag + four checkout sources) and
      `program-tuple.yaml` `dotfiles-assets` are `v0.13.0`.
- [ ] The skins verify plane accepts four manifests (`glass`, `flat`, `paper`,
      `terminal`) and expands all seven `*.gtk.css.j2` templates for every
      manifest × mode.
- [ ] Verify retains the v2 checks: `schemaVersion = 2`, name matching the
      file, nested `groups.surface/state/type/ink/layout`, optional mode
      overrides, the resolved `tokens.json` appearance-json contract and the
      vendored contracts PIN `v0.7.0` with sha256 values.
- [ ] The `terminal` manifest's dense values are checked structurally
      (`surface.panel.radius = 0`, `type.font-family` contains `monospace`).
- [ ] `[groups.layout.ags-capture]` and `[groups.layout.ags-btop-studio]` are
      absent from every deployed manifest; missing optional layout groups are
      not failures.
- [ ] Hardcoded `v0.12.2` fixtures/tests move to `v0.13.0`; a terminal-skin
      verify test proves a valid terminal manifest passes and a tampered
      terminal manifest fails.
- [ ] `make gates`, `make ci-gates-parity` and local-corpus assets parity
      against `/home/inumaki/Development/dotfiles/dotfiles-assets` pass.
- [ ] Engine `0.1.40` + CHANGELOG; annotated tag `v0.1.40` after the
      fast-forward merge; push `main` and the tag; no apply.

## Evidence / Verify

Worktree `.worktrees/REQ-026/`, branch
`ticket/REQ-026-assets-v013-terminal`.

(Filled in by the implementation and evidence commits.)
