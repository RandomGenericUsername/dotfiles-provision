---
id: REQ-041
title: "Mirror contracts v0.11.0 and assets v0.18.0 (host rectangle radii)"
kind: requirement
status: in-progress
lane: 1
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-041/
branch: ticket/REQ-041-host-rectangle-radii-pin
---

# Mirror contracts v0.11.0 and assets v0.18.0

## Requirement

Pin-only slice: mirror contracts `v0.11.0` and dotfiles-assets `v0.18.0`
everywhere in engine vars, composition fixtures and tests, and keep the
released skin envelope intact (five manifests, eleven templates, ten CSS
targets, one rofi `rasi` artifact).

1. Move every `*_assets_pinned_tag` mirror and the composition fixture
   (`assets.yaml`, `program-tuple.yaml`) to assets `v0.18.0`; move
   `verify_generation_contract_tag` and `verify_skins_expected_contract_tag`
   to contracts `v0.11.0`.
2. Vendor the contracts `v0.11.0` generation-manifest schema and fixtures.
   Preserve the host fixture and add the host-rectangle fixture plus the
   pill-radius negative fixture.
3. Keep `scripts/pin-audit.py` fail-closed and audit the same skin/target/
   artifact sets for assets `v0.18.0`.
4. Run the pin-only lane `make gates-pin` plus targeted skin/verify/contracts
   tests; record the gate choice.
5. Tag/push/release `v0.1.61` with only the wheel and sdist.

No runtime/assets/composition/app edits, no live state writes, no apply.

## Acceptance

- [ ] Engine pins and fixtures mirror assets `v0.18.0` / contracts `v0.11.0`.
- [ ] Contracts `v0.11.0` generation schema and rectangle fixtures are vendored.
- [ ] Pin audit stays fail-closed with the unchanged skin envelope.
- [ ] `make gates-pin` and targeted tests pass; gate choice recorded.
- [ ] Engine `0.1.61` tagged/released with only wheel/sdist; no apply.
