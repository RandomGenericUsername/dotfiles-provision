---
id: REQ-049
title: "Mirror assets v0.20.1 and bar v0.6.5 (sound panel QA)"
kind: requirement
status: done
lane: 1
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-049/
branch: ticket/REQ-049-sound-panel-qa
---

# Mirror assets v0.20.1 and bar v0.6.5

Pin-only lane. Move the engine assets mirror to **v0.20.1** (bare icon-only
sound controls, thumbnail styles) and the app inventory bar tag to **v0.6.6**
(sound panel QA; v0.6.6 fixes the artwork-cache mkdir and header alignment). Contracts `v0.12.0`, platform `v1.1.0`, runtime ownership and
the other six app tags are unchanged.

1. Every `*_assets_pinned_tag` + `verify_assets_pinned_tag` → v0.20.1.
2. Composition fixtures, app-list fixture, hardcoded pin assertions and
   `scripts/pin-audit.py` → v0.20.1 / bar v0.6.5.
3. Release metadata 0.1.66 (pyproject + uv.lock) and CHANGELOG.
4. Gates: `make gates-pin`, `make assets-parity`, `make build`, lock/docs.
5. Tag/push `v0.1.66`.

## Acceptance

- [x] Every assets mirror is v0.20.1 and the bar inventory tag is v0.6.6; the
      other pins are unchanged.
- [x] `make gates-pin`, `make assets-parity`, `make build`, `make lock-check`
      and `make docs-check` pass.
- [x] `v0.1.66`/`v0.1.67` tagged/pushed; no apply.

## Evidence

- Worktree `.worktrees/REQ-049/`, branch `ticket/REQ-049-sound-panel-qa`,
  based on `5997091` (v0.1.65).
- `make gates-pin` PASS (pin-audit assets=v0.20.1, apps bar v0.6.5).
- `make assets-parity` PASS on the released assets v0.20.1.
- `make build` PASS: `dotfiles_provision-0.1.66` sdist + wheel.
