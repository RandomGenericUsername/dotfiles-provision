---
id: REQ-060
title: "Expose the Neovim palette link (optional consumer)"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-060/
branch: ticket/REQ-060-nvim-palette-link
---

# Expose the Neovim palette link (optional consumer)

## Requirement

1. Add `state_links_optional_consumers` with
   `{ base: palette, spine: nvim/lua/dotfiles-palette.lua, target: colors.nvim.lua }`.
2. Create the link in the same stable-link task as the required consumers, but
   exclude it from the resolve assertion (the artifact is optional during the
   staged rollout).
3. Keep the required consumer table unchanged.
4. No tag/release/pin bump in this phase.

## Acceptance

- [x] Optional consumer entry added.
- [x] Link creation includes optional consumers; resolve assertion does not.
- [x] `test_v3_locality.py` locks the optional table.
- [x] No tag/release/pin bump.

## Evidence

- `ansible/roles/state_links/vars/main.yml`: required + optional tables.
- `ansible/roles/state_links/tasks/main.yml`: link loops use the union;
  resolve loop stays required-only.
- `tests/unit/test_v3_locality.py::TestStableConsumerLinks` updated.


- Release: https://github.com/RandomGenericUsername/dotfiles-provision/releases/tag/v0.1.92
