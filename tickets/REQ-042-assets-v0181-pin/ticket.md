---
id: REQ-042
title: "Mirror dotfiles-assets v0.18.1 (rofi generated appearance last)"
kind: requirement
status: in-progress
lane: 1
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-042/
branch: ticket/REQ-042-assets-v0181-pin
---

# Mirror dotfiles-assets v0.18.1

## Requirement

Pin-only slice: mirror dotfiles-assets `v0.18.1` everywhere in engine vars,
composition fixtures and tests. Contracts stay `v0.11.0` (`v0.18.1` re-ships
the same vendored contracts pin).

1. Move every `*_assets_pinned_tag` mirror and the composition fixture
   (`assets.yaml`, `program-tuple.yaml`) to assets `v0.18.1`.
2. Keep `scripts/pin-audit.py` fail-closed over the same released skin
   envelope: five manifests, ten CSS targets, one rofi `rasi` artifact.
3. Update hardcoded pin assertions and fixture source refs; leave the
   contracts pin/schema fixtures untouched.
4. Run `make gates-pin` plus targeted assets/verify/pin tests, docs-check,
   parity and the build/wheel check.
5. Tag/push/release `v0.1.62` with only the wheel and sdist.

No runtime/assets/composition/app edits, no live state writes, no apply.

## Acceptance

- [ ] Engine pins and fixtures mirror assets `v0.18.1`; contracts stay `v0.11.0`.
- [ ] Pin audit keeps the same fail-closed skin/target/artifact sets.
- [ ] `make gates-pin` and targeted assets/verify/pin tests pass; docs-check,
      parity and build/wheel check pass.
- [ ] Engine `0.1.62` tagged/released with only wheel/sdist; no apply.
