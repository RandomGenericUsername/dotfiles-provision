---
id: REQ-071
title: "Mirror dotfiles-assets v1.0.0 (icons schema_major 2 corpus release)"
kind: requirement
status: in-progress
lane: direct
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-071/
branch: ticket/REQ-071-assets-v100
---

# Mirror dotfiles-assets v1.0.0

The composition moved its `assets.tag` to `dotfiles-assets v1.0.0` (the
`schema_major 2` icons corpus release, REQ-149 in `dotfiles-assets`), and its
`make deploy-coverage` now fails because the engine mirror still says
`v0.22.6`:

```
FAIL: ansible/roles/assets/vars/main.yml: assets_pinned_tag 'v0.22.6' must mirror 'v1.0.0'
```

Mirror the corpus tag in every engine role var, the composition fixture, the
pin audit and the hardcoded assertions, then release the engine.

## Requirement

- Every `*_assets_pinned_tag` role mirror and the composition fixture
  (`assets.yaml`, `program-tuple.yaml`) name `v1.0.0`; the fixture's four
  checkout `source:` paths resolve under `assets/v1.0.0/`.
- `make gates-pin` is green (pin-audit, lint, docs-check, CI parity).
- The full release gates are green; `make assets-parity` clones `v1.0.0` and
  the template-vars parity module executes with zero skips.
- Release engine `v0.1.103`; the composition can pin it.

Out of scope: the `contracts` tuple pin (`v0.12.0`) is tracked separately from
the corpus tag and is not changed here.

## Acceptance

- [ ] No active `v0.22.6` assets-pin mirror remains in `ansible/`, `tests/` or
      the CHANGELOG forward path.
- [ ] `make gates-pin` exits 0.
- [ ] `make gates` exits 0.
- [ ] `make assets-parity` exits 0 with 0 skipped tests.
- [ ] Annotated tag `v0.1.103` created and `git describe --tags` reports it.
