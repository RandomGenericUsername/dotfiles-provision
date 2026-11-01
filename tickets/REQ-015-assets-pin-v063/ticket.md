---
id: REQ-015
title: "Consume dotfiles-assets v0.6.3 (semantic-role icon mappings)"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-015/
branch: ticket/REQ-015-assets-pin-v0-6-3
---

# Consume dotfiles-assets v0.6.3

## Requirement

dotfiles-assets `v0.6.3` re-pins every icon mapping from the CSG-era `colorN`
carriers to semantic tpr roles plus `on_backdrop`, makes `defaults.yaml` real,
declares `surface:` classes, and empties the legacy baseline (REQ-008 Phase B).
This ticket moves the engine and composition pins onto that corpus and updates
every mirrored expectation.

## Acceptance

- [ ] Engine mirrors bumped: `assets_pinned_tag`, `verify_assets_pinned_tag`,
      `btop_config_assets_pinned_tag`, plus the compositor/config/kitty/display/
      wlogout/zsh role mirrors — all `v0.6.3`.
- [ ] Fixture composition manifests (assets, program-tuple) and every test
      expectation moved to `v0.6.3`; the `v0.6.2` autostart fixture filename is
      kept because its content is unchanged.
- [ ] `rg -n 'v0\.6\.2' ansible tests` returns only the intentional autostart
      fixture references.
- [ ] Engine gates green; version `0.1.29`; tag after orchestrator review.
- [ ] Live bootstrap renders icons from semantic roles (no `colorN` in the
      deployed mappings) and doctor stays clean.

## Known debt (follow-up, not this ticket)

The corpus pin is still mirrored in multiple roles and the program tuple
(`assets`, `verify`, `btop_config`, `compositor_configs`, `config_copies`,
`display_manager`, `kitty_config`, `wlogout_config`, `zsh_config`). Single-sourcing
the corpus pin from `assets.yaml` (like `cli_tools_tags`) removes these mirrors;
tracked separately so this pin bump stays mechanical.

## Evidence / Verify

- Evidence: dotfiles-assets tag `v0.6.3`; `make validate-icons` →
  `legacy_baseline=0`, 51 roles, 58 wallpaper variants held to `on_backdrop`.
- Verify: `rg -n 'v0\.6\.2' ansible tests`; `make gates`; bootstrap + `itr render`.
