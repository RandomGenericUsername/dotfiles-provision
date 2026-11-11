---
id: REQ-043
title: "Mirror contracts v0.12.0, assets v0.19.0, ags-platform v1.1.0 and ags-bar v0.6.2 (window role + kitty conf)"
kind: requirement
status: in-progress
lane: 1
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-043/
branch: ticket/REQ-043-window-kitty-platform-mirror
---

# Mirror the window-role / kitty release tuple

## Requirement

Mirror the released window-role slice into the engine and provision the kitty
generated-appearance consumer. Runtime stays composition-owned (not an engine
pin). Only the bar app tag moves.

1. **Pins.** contracts `v0.12.0`, assets `v0.19.0`, ags-platform `v1.1.0`,
   ags-bar `v0.6.2`; every other app tag and runtime pin is unchanged. Update
   every role mirror, verify mirror, composition fixture
   (`program-tuple.yaml`, `assets.yaml`, `apps.yaml`), app-list fixture,
   `scripts/pin-audit.py` expected sets and hardcoded test assertions.
2. **Vendored contracts.** Replace the engine's contracts fixture with
   `v0.12.0`: generation/appearance schemas plus window host fixtures and the
   refreshed PIN digests.
3. **Engine verify.**
   - accept the required `surface.window` group (eight tokens, unitless
     `[0,1]` opacity) in every deployed skin manifest;
   - accept generation `host.defaults` window radius/border-width alongside
     the existing panel/card/control/cell paths;
   - skin envelope: 5 manifests, 12 templates (10 CSS targets + `kitty.conf.j2`
     and `rofi.rasi.j2` artifacts), 10 CSS targets, artifacts `kitty:conf` and
     `rofi:rasi`;
   - pin audit expected manifest/target/artifact sets match that envelope.
4. **Kitty provisioning.**
   - add the stable link
     `config/kitty/appearance.conf -> state/current/appearance/kitty.conf`;
   - the rendered static kitty config imports the runtime palette
     (`colors.kitty`) first, the generated `appearance.conf` second and the
     user `local.conf` last, keeping `auto_reload_config -1` and the
     app-owned structure otherwise unchanged;
   - verify the raw link, its resolution, the import order and the generated
     conf's presence.
5. **Tests.** state_links/verify/locality kitty positive and negative cases;
   window-schema/opacity acceptance and rejection; bar `v0.6.2`; full gates
   plus assets parity.
6. **Release.** Tag/push/release `v0.1.63` with only the wheel and sdist.

No runtime/assets/composition/app edits, no live state writes, no apply.

## Acceptance

- [ ] Every engine pin and fixture mirrors contracts `v0.12.0`, assets
      `v0.19.0`, platform `v1.1.0`, bar `v0.6.2`; all other pins unchanged.
- [ ] Contracts `v0.12.0` generation/appearance schemas and fixtures are
      vendored with matching PIN digests.
- [ ] Verify accepts the required window role/opacity and window host defaults;
      the skin envelope is 5/12/10 with `kitty:conf` + `rofi:rasi`.
- [ ] Kitty static import order, `appearance.conf` stable link/resolution and
      generated-conf presence are provisioned and verified, with positive and
      negative tests.
- [ ] Full gates + assets parity pass.
- [ ] Engine `0.1.63` tagged/released with only wheel/sdist; no apply.

## Evidence

(Filled at close.)

## Commits

- plan commit — ticket + INDEX
