---
id: REQ-043
title: "Mirror contracts v0.12.0, assets v0.19.0, ags-platform v1.1.0 and ags-bar v0.6.2 (window role + kitty conf)"
kind: requirement
status: done
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

- [x] Every engine pin and fixture mirrors contracts `v0.12.0`, assets
      `v0.19.0`, platform `v1.1.0`, bar `v0.6.2`; all other pins unchanged.
- [x] Contracts `v0.12.0` generation/appearance schemas and fixtures are
      vendored with matching PIN digests.
- [x] Verify accepts the required window role/opacity and window host defaults;
      the skin envelope is 5/12/10 with `kitty:conf` + `rofi:rasi`.
- [x] Kitty static import order, `appearance.conf` stable link/resolution and
      generated-conf presence are provisioned and verified, with positive and
      negative tests.
- [x] Full gates + assets parity pass.
- [x] Engine `0.1.63` tagged/released with only wheel/sdist; no apply.

## Evidence

Gate choice: **full `make gates`** (`test lint hermetic lock-check
docs-check`) because this slice changes verify behavior/schema acceptance and
adds the kitty provisioning path. `make assets-parity` was run against the real
pinned corpus.

| Gate | Result |
| --- | --- |
| `make gates` | PASS (rc `0`; all five gates) |
| test | `1026 passed, 35 skipped, 86 deselected` |
| hermetic | `1023 passed, 38 skipped, 86 deselected` |
| lint | `All checks passed!` |
| lock-check | `uv lock --check` clean |
| docs-check | clean |
| ci-gates-parity | `PASS gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test']` |
| pin-audit | `PASS (assets=v0.19.0, contracts=v0.12.0, platform=v1.1.0, apps=7, skins=5, targets=10, artifacts=2)` |
| assets-parity | `PASS assets-parity: 10 tests executed, 0 skipped` (`dotfiles-assets @ v0.19.0`) |
| build | `dotfiles_provision-0.1.63.tar.gz` + `dotfiles_provision-0.1.63-py3-none-any.whl`; `check-wheel-contents.py` PASS |

Targeted kitchen-sink evidence:

```text
pytest tests/unit/test_kitty_config_role.py tests/unit/test_template_vars_parity.py
       tests/unit/test_compositor_skeleton_configs.py
# 33 passed

pytest tests/unit/test_verify_role.py tests/unit/test_v3_locality.py
       tests/unit/test_pin_audit.py -m "not integration"
# 173 passed, 44 deselected

pytest tests/unit/test_verify_role.py::TestVerifyConsumerLinkRender -m integration
# 23 passed (includes the kitty appearance.conf missing / dangling /
# wrong-target / generation-path negatives and the passing topology)
```

Build artifacts:

```text
eb1bb672bc43c9f1f86e64ba7cc38ba04296c8648dab8fc721d087dd0ec4d055  dotfiles_provision-0.1.63-py3-none-any.whl
cf45dfbf50ccaaf2d2372c560e13dd96ad8fa0ea66ef9cc1c7c725baad9d15e6  dotfiles_provision-0.1.63.tar.gz
```

Exact engine pins and fixture mirrors:

- installer **v0.1.63** (this release), contracts **v0.12.0**, assets
  **v0.19.0**, platform **v1.1.0**, tpr **v0.4.0** (unchanged).
- apps: bar **v0.6.2**, notifications **v0.5.1**, capture **v0.7.1**,
  clipboard **v0.6.1**, wallpaper-selector/icme/btop-theme-studio **v0.5.1**
  (only bar moves).
- runtime is composition-owned; the engine has no runtime pin to move.
- skin envelope: 5 manifests (`glass`, `flat`, `paper`, `terminal`,
  `terminal-host`), 12 templates (10 `<configDir>.gtk.css.j2` CSS targets +
  `kitty.conf.j2` and `rofi.rasi.j2` artifacts), 10 CSS targets, artifacts
  `kitty:conf` + `rofi:rasi`.
- contracts fixtures: `tests/fixtures/contracts/v0.12.0` carries the
  generation/appearance schemas and the window host fixtures with PIN digests.

Kitty provisioning (exact):

```text
stable link:
  <install>/config/kitty/appearance.conf
    -> <state>/dotfiles/current/appearance/kitty.conf

rendered static kitty.conf order:
  include <state>/dotfiles/current/colors.kitty
  include appearance.conf
  include local.conf
  auto_reload_config -1
```

The corpus body keeps ownership of the static structure; provisioning renders
it to a deterministic scratch path and assembles the final file with the one
`appearance.conf` hop. The scratch render/removal are internal (not change
reporters); the final `copy` is idempotent, so a second run reports `changed=0`.
Verify asserts the raw link target, resolution through `current`, the first
token being the absolute `colors.kitty` include, the `colors -> appearance ->
local` order, and the presence of `current/appearance/kitty.conf`.

Composition pins needed downstream (read-only note; no downstream edits):

- contracts **v0.12.0**, assets **v0.19.0**, ags-platform **v1.1.0**,
  dotfiles-runtime **v1.5.0**, dotfiles-provision installer **v0.1.63**,
  apps bar **v0.6.2**; all other app tags unchanged.

No apply, no runtime/assets/composition/app edits and no live state writes.

## Commits

- `7c5515d` — plan commit (ticket + INDEX)
- `5f212f8` — mirror pins/fixtures, window verify, kitty provisioning
- `ea49ded` — first kitty idempotence correction (superseded by `17ce1c9`)
- `89a5f2e` — release `0.1.63` metadata
- `17ce1c9` — keep the kitty corpus render/final assembly idempotent
- `5e676d9` — absolute kitty palette path in the verify fixture
- evidence close commit follows; tag `v0.1.63`
