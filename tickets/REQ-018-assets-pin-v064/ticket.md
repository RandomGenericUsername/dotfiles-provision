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

- [ ] All `*_assets_pinned_tag` mirrors = v0.6.4 (assets, verify, btop,
      compositor, config_copies, display, kitty, wlogout, zsh).
- [ ] Fixture manifests (assets sources, program tuple) = v0.6.4.
- [ ] Tests updated; `make gates` green; engine v0.1.32 released.
- [ ] Live bootstrap deploys the rofi config; rofi follows the wallpaper.

## Known debt

The corpus pin remains mirrored across roles; single-sourcing it from
`assets.yaml` is the follow-up (same class as REQ-014 for CLI pins).

## Outcome

Released engine `v0.1.32`, deployed via PIN-0130 on 2026-11-04 (verify green,
291 tasks). Live proof:
- assets pin `v0.6.4`; deployed rofi config has zero carrier tokens and uses
  `@surface-container`/`@surface-container-high`/`@primary`/`@primary-container`;
- `rofi -dump-theme` resolves role values that change with the wallpaper:
  default `primary rgba(185,195,255)` / `surface-container rgba(31,31,37)` →
  eagle `rgba(255,181,154)` / `rgba(39,29,26)` → restored back;
- bar refresh in the same cycle: `status: applied`, `mode: restart`.
