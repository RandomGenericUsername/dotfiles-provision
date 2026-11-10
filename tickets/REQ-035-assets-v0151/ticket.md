---
id: REQ-035
title: "Mirror dotfiles-assets v0.15.1 (wlogout static ownership fix)"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-035/
branch: ticket/REQ-035-assets-v0151
---

# Mirror dotfiles-assets v0.15.1 (wlogout static ownership fix)

## Requirement

`dotfiles-assets v0.15.1` fixes the wlogout static stylesheet so generated skin
paint/rhythm actually wins (W-2.6): the static template keeps only wallpaper,
icons, layout/motion, and no longer renders `SYSTEM_FONT_FAMILY` or
`FONT_SIZE_PX`. The engine at `v0.1.52` still mirrors assets `v0.15.0`, so the
host-defaults composition cutover cannot use `v0.15.1`.

Mirror assets `v0.15.1` everywhere, adopt the 3-variable wlogout render context,
and keep contracts `v0.9.0`, runtime-independent behavior, and the host-bearing
generation verify unchanged.

## Acceptance

- [x] Every engine assets pin/mirror and composition fixture moves to `v0.15.1`.
- [x] `wlogout_config` renders only the 3 variables required by the released
      `style.css.tpl` (`COLORS_FILE_PATH`, `STATE_ROOT`,
      `CURRENT_WALLPAPER_SYMLINK`); the font variables are removed.
- [x] The rendered static style still imports palette first and
      `appearance.css` last; verify passes against the released assets corpus.
- [x] Contracts `v0.9.0`, generation `version: 3`, host fixture and v3 locality
      checks are unchanged.
- [x] `make gates` and `make ci-gates-parity` pass; engine `0.1.53`, annotated
      tag `v0.1.53`, GitHub Release with only its wheel/sdist; no apply.

## Evidence

Implementation `8e54c86`; mirrors `dotfiles-assets v0.15.1` everywhere, adopts
the 3-variable wlogout render context, and removes the obsolete font vars.
No behavior change beyond the released static template and pin mirrors.

- `make gates` → rc 0
  - `test`: **987 passed, 33 skipped, 67 deselected** in 2120.95s
  - `lint`: **All checks passed**
  - `hermetic`: **984 passed, 36 skipped, 67 deselected** in 2030.76s
  - `lock-check`: **Resolved 33 packages**
  - `docs-check`: rc 0
- `make ci-gates-parity` →
  `PASS gates=['docs-check','hermetic','lint','lock-check','test']`.
- `wlogout_config` render context is exactly `COLORS_FILE_PATH`, `STATE_ROOT`,
  `CURRENT_WALLPAPER_SYMLINK`; the fast role test passes.
- Release: engine `0.1.53`, annotated tag `v0.1.53`, GitHub Release with only
  its wheel/sdist; no apply.

## Evidence / Verify

`make gates`, `make ci-gates-parity`; targeted wlogout/verify/assets tests.
