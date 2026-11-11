---
id: REQ-040
title: "Phase 3A-4 format-aware skin consumers (GTK3/GTK4/rofi links + imports)"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-040/
branch: ticket/REQ-040-skin-consumer-phase3a4
---

# Phase 3A-4 format-aware skin consumers

## Requirement

Provision the format-aware consumer plane designed in
`dotfiles-v3/docs/110-format-aware-skin-consumers.md` §5 against contracts
`v0.10.0`, assets `v0.17.0` and runtime `v1.3.0`:

1. Mirror assets `v0.17.0` and contracts `v0.10.0` in every engine pin,
   composition fixture and test. Vendor the contracts `v0.10.0` generation
   schema (optional `appearance.artifacts`) and move
   `verify_generation_contract_tag` / `verify_skins_expected_contract_tag` and
   the schema-envelope fixtures to `v0.10.0`.
2. `state_links` gains provisioning-owned appearance links:
   `config/gtk-3.0/appearance.css -> current/appearance/gtk3.css`,
   `config/gtk-4.0/appearance.css -> current/appearance/gtk4.css`,
   `config/rofi/appearance.rasi -> current/appearance/rofi.rasi`, through the
   same create-then-assert flow.
3. Static imports: GTK3/GTK4 `gtk.css` import `appearance.css` after the
   palette import; rofi `config.rasi` imports `appearance.rasi` after its one
   palette import. App-owned rules and structure stay intact.
4. Verify accepts the assets v0.17.0 envelope (five manifests, ten CSS targets
   plus the rofi `rasi` artifact), asserts the committed generation targets and
   artifacts, the three stable links, and rejects generation/app-tag routes.
   A `.rasi` artifact is never validated as CSS.
5. Tests cover state links, verify/locality, GTK/rofi render + import ordering,
   missing/dangling/wrong-target/generation-path negatives, and contracts
   v0.10.0 fixtures.

No apply, no runtime/assets/composition/contract edits, no live state writes.

## Acceptance

- [ ] Engine pins and fixtures mirror assets `v0.17.0` / contracts `v0.10.0`.
- [ ] Contracts `v0.10.0` generation schema and fixtures are vendored.
- [ ] GTK3/GTK4/rofi appearance links are created and verified raw/resolved.
- [ ] GTK `gtk.css` and rofi `config.rasi` import generated appearance last.
- [ ] Verify accepts the v0.17.0 envelope and asserts generation artifacts.
- [ ] Negative link/ordering tests pass.
- [ ] Full `make gates` and `make ci-gates-parity` pass; evidence recorded.
- [ ] Engine `0.1.60` tagged/released with only wheel/sdist; no apply.
