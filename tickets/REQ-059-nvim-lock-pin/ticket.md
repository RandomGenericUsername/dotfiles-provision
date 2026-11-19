---
id: REQ-059
title: "Pin assets v0.21.7 (resolved LazyVim lock)"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-059/
branch: ticket/REQ-059-nvim-lock-pin
---

# Pin assets v0.21.7 (resolved LazyVim lock)

## Why

`dotfiles-assets v0.21.7` refreshes `configs/nvim/lazy-lock.json` to the stable
plugin set LazyVim resolves on first launch. The engine must mirror that tag so
the next provision copies the resolved lock instead of the pre-resolution one.

## Requirement

1. Move every engine assets pin/fixture/assertion from `v0.21.6` to `v0.21.7`.
2. Release metadata `0.1.91` (pyproject + `__version__` + uv.lock + CHANGELOG).
3. `make gates-pin`, `make build`, `make release-preflight TAG=v0.1.91` pass.
4. Tag/release `v0.1.91`.

## Acceptance

- [ ] Active engine pins and fixtures are `v0.21.7`.
- [ ] `make gates-pin` PASS.
- [ ] `make build` PASS.
- [ ] `make release-preflight TAG=v0.1.91` PASS.
- [ ] `v0.1.91` tagged/pushed/released.
