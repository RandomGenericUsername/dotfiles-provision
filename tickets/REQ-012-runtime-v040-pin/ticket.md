---
id: REQ-012
title: "Pin dotfiles-runtime v0.4.0 (producer seam)"
kind: requirement
status: done
lane: 1
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-012/
branch: ticket/REQ-012-runtime-v040-pin
---

# Pin dotfiles-runtime v0.4.0

## Requirement

Move the runtime pin from `v0.3.0` to `v0.4.0`; nothing else changes.

- `cli_tools` vars + fixture manifest: `dotfiles-runtime` tag `v0.4.0`.
- `verify_runtime_version`: `v0.4.0`.
- Test literals asserting the runtime tag.
- Engine version `0.1.26`.

v0.4.0 adds the palette producer seam (`TprAdapter`, `THEME__` allowlist, producer fingerprint in
the cache key, `RUNTIME__PALETTE__PRODUCER` default `csg`). Keep csg/weg/itr/tpr pins unchanged.

## Acceptance

- [ ] Runtime mirrors are `v0.4.0`; no runtime `v0.3.0` literal remains.
- [ ] Targeted pin/role tests green; full gate run recorded.
- [ ] Engine version `0.1.26` in `pyproject.toml`/`src/provisioning/__init__.py` and `CHANGELOG.md`.
- [ ] No dotfiles-v3 edits; no producer activation.

## Evidence

- dotfiles-runtime `v0.4.0` tag pushed.
- Engine `v0.1.25` runtime pin surfaces.
