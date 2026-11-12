---
id: REQ-044
title: "Mirror the parity app releases in the engine final inventory (bar v0.6.4 note v0.6.3 sound-panel)"
kind: requirement
status: in-progress
lane: 1
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-044/
branch: ticket/REQ-044-app-parity-inventory-pin
---

# Mirror the parity app releases

## Requirement

Pin-only lane. Update the engine's final app inventory to the parity releases;
contracts `v0.12.0`, assets `v0.19.0`, platform `v1.1.0` and runtime ownership
stay unchanged.

1. **App inventory.** bar `v0.6.4`, notifications `v0.5.2`, capture `v0.7.2`,
   clipboard `v0.6.2`, wallpaper-selector `v0.5.2`, icme `v0.5.2`,
   btop-theme-studio `v0.5.2`. `v0.6.3` is the bar sound-panel release; the
   final inventory pins `v0.6.4`.
2. **Mirrors.** Update
   `tests/fixtures/ags-apps/app-list/all-standalone.apps.yaml`,
   `tests/fixtures/composition/dotfiles/provisioning/apps.yaml`, hardcoded
   app-tag assertions (`tests/unit/test_ags_apps_units_role.py`) and
   `scripts/pin-audit.py` expected inventory.
3. **Superseded releases note.** Add an explicit documentation note that engine
   tags `v0.1.54` and `v0.1.55` are immutable mistakes, must not be used, and
   that `v0.1.56+`/`v0.1.64` are authoritative.
4. **Gates.** Run `make gates-pin`, targeted app inventory/pin tests,
   docs-check, assets parity, and the wheel/sdist build.
5. **Release.** Tag/push/release `v0.1.64` carrying only the wheel and sdist.

No apply, no downstream edits, no runtime/assets/composition/app edits.

## Acceptance

- [ ] Every app inventory mirror carries the parity tags; contracts/assets/
      platform pins are unchanged.
- [ ] `make gates-pin`, targeted app inventory/pin tests, docs-check, assets
      parity and the build/wheel checks pass.
- [ ] The superseded `v0.1.54`/`v0.1.55` note is present and explicit.
- [ ] Engine `0.1.64` is tagged/released with only wheel/sdist; no apply.

## Evidence

Pending gate run.

## Commits

- plan commit (ticket + INDEX) follows
