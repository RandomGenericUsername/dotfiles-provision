---
id: REQ-011
title: "Pin theme-producer v0.2.0 (prefer/fallback, lightness, light mode)"
kind: requirement
status: in-progress
lane: 1
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-011/
branch: ticket/REQ-011-tpr-v020-pin
---

# Pin theme-producer v0.2.0

## Requirement

Move every tpr pin mirror from `v0.1.0` to `v0.2.0`; nothing else changes.

- `cli_tools` vars + fixture manifest entry.
- `settings_tpr_image_tag` + rendered settings.
- `assets_tpr_pinned_tag` + template source.
- `verify_tpr_version` + the three image references.
- Any test literal that asserts the tpr tag.

v0.2.0 adds the source preferences, lightness controls and light-mode projections; the image tags
are `v0.2.0`. Keep csg/weg/itr/runtime pins unchanged.

## Acceptance

- [ ] All tpr mirrors are `v0.2.0`; no tpr `v0.1.0` literal remains.
- [ ] `make test` (or the targeted pin/role suites) green; a full gate run recorded.
- [ ] Engine version 0.1.23 in `pyproject.toml`/`src/provisioning/__init__.py` and `CHANGELOG.md`.
- [ ] No dotfiles-v3 edits; no default producer flip.

## Evidence

- theme-producer `v0.2.0` tag pushed.
- Engine `v0.1.22` tpr pin surfaces.
