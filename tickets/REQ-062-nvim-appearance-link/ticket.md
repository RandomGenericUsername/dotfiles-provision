---
id: REQ-062
title: "Expose the Neovim appearance tokens link (required consumer)"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-062/
branch: ticket/REQ-062-nvim-appearance-link
---

# Expose the Neovim appearance tokens link (required consumer)

## Requirement

`dotfiles-v3` REQ-124 feeds Neovim's appearance loader from the mandatory
`state/current/appearance/tokens.json`. Provisioning already owns the stable
non-runtime links; add the Neovim appearance document as a REQUIRED consumer:

1. Add
   `{ base: appearance, spine: nvim/lua/dotfiles-appearance.json, target: tokens.json }`
   to `state_links_consumers` (the resolved set) — not to
   `state_links_optional_consumers`, because `tokens.json` is mandatory in every
   committed v3 generation (`appearance.tokensPath`).
2. Ensure the link parent `config/nvim/lua` is created (the role's parent task
   loops the consumer union; the optional palette link already names that dir).
3. Mirror the same entry in `verify_consumer_symlinks`.
4. Lock the addition in `tests/unit/test_v3_locality.py` and
   `tests/unit/test_verify_role.py`.
5. No tag/release/pin bump and no host mutation in this phase.

## Acceptance

- [ ] Required consumer entry added; optional table unchanged.
- [ ] Link parent `config/nvim/lua` is provisioned.
- [ ] `verify_consumer_symlinks` mirrors the entry.
- [ ] Locality/verify tests cover the link.
- [ ] Targeted tests, `gates-pin`, and lint pass.
- [ ] No tag/release/pin bump.

## Evidence

- `ansible/roles/state_links/vars/main.yml`: required consumer table.
- `ansible/roles/verify/vars/main.yml`: `verify_consumer_symlinks`.
- `tests/unit/test_v3_locality.py`, `tests/unit/test_verify_role.py`.
