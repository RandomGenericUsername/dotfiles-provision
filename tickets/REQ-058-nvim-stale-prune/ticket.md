---
id: REQ-058
title: "Prune retired Neovim config files on the LazyVim cutover"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-058/
branch: ticket/REQ-058-nvim-stale-prune
---

# Prune retired Neovim config files on the LazyVim cutover

## Why

`config_copies` copies the pinned `configs/nvim` directory into the spine with
`ansible.builtin.copy`, which does not delete files absent from the source.
After `dotfiles-assets v0.21.6` (LazyVim), the old hand-rolled files survived on
hosts that had the previous config:

- `lua/options.lua`
- `lua/plugins/catppuccin.lua`
- `lua/plugins/lsp-config.lua`
- `lua/plugins/lualine.lua`
- `lua/plugins/neo-tree.lua`
- `lua/plugins/telescope.lua`
- `lua/plugins/treesitter.lua`

The new `lua/config/lazy.lua` imports `plugins`, so the stale plugin specs are
loaded beside the LazyVim overrides. That is a real deployment defect, not a
check-mode artifact.

## Requirement

1. Add `config_copies_retired_nvim_files` (the seven relative paths above) to
   `ansible/roles/config_copies/vars/main.yml`, documented as the LazyVim
   migration cleanup.
2. After the directory/per-file copies, remove those paths from
   `<install>/config/nvim/` with `ansible.builtin.file` `state: absent`.
   The task is `when: not ansible_check_mode` (a dry run never mutates).
3. Add a role test asserting the retired list and the prune task (loop, state,
   check-mode gate).
4. Release metadata `0.1.90` and a CHANGELOG entry.

## Forbidden

- No change to the assets corpus (still `v0.21.6`).
- No pin bump beyond the patch release (assets stay `v0.21.6`).
- No host apply in this implementation phase.

## Acceptance

- [ ] The seven retired files are removed on an apply.
- [ ] A dry run does not delete anything.
- [ ] The role test locks the list and the task shape.
- [ ] Targeted config-copy tests and lint pass.
- [ ] No tag/release until the user's green.

## Evidence

- Copy task leaves extra files:
  `ansible/roles/config_copies/tasks/main.yml` (directory `copy`).
- Live host after `v0.21.6` bootstrap contained both the new `lua/config/*`
  and the seven old files.
- New loader imports `plugins`:
  `dotfiles-assets/configs/nvim/lua/config/lazy.lua`.
