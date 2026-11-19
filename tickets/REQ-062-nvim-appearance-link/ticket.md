---
id: REQ-062
title: "Expose the Neovim appearance tokens link (required consumer)"
kind: requirement
status: done
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

- [x] Required consumer entry added; optional table unchanged.
- [x] Link parent `config/nvim/lua` is provisioned.
- [x] `verify_consumer_symlinks` mirrors the entry.
- [x] Locality/verify tests cover the link.
- [x] Targeted tests, `gates-pin`, and lint pass.
- [x] No tag/release/pin bump.

## Evidence

- `ansible/roles/state_links/vars/main.yml`: required consumer table gains
  `{ base: appearance, spine: nvim/lua/dotfiles-appearance.json, target: tokens.json }`;
  `state_links_optional_consumers` is unchanged.
- `ansible/roles/state_links/tasks/main.yml`: the parent-directory task loops the
  required+optional union, so `config/nvim/lua` is created.
- `ansible/roles/verify/vars/main.yml`: `verify_consumer_symlinks` mirrors the entry.
- `tests/unit/test_v3_locality.py`, `tests/unit/test_verify_role.py`: exact
  consumer lists, post-seed expectations and the verify negative fixture include
  the link.

Commands (worktree `.worktrees/REQ-062/`):

- `uv run pytest -q tests/unit/test_v3_locality.py tests/unit/test_verify_role.py::TestVerifyConsumerLinks`
  → `30 passed`.
- `uv run pytest -q tests/unit/test_verify_role.py::TestVerifyConsumerLinkRender tests/unit/test_verify_role.py::TestVerifyVars`
  → `72 passed, 1 failed`; the failure is the pre-existing baseline
  `test_passing_topology_renders_the_consumer_assert` (GloView unit absent from
  the synthetic machine, reproduces unchanged on `main`).
- `make gates-pin` → pin-audit PASS, ruff clean, CI parity PASS.



- Release: v0.1.94
