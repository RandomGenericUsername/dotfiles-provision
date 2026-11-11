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

- [x] Engine pins and fixtures mirror assets `v0.17.0` / contracts `v0.10.0`.
- [x] Contracts `v0.10.0` generation schema and fixtures are vendored.
- [x] GTK3/GTK4/rofi appearance links are created and verified raw/resolved.
- [x] GTK `gtk.css` and rofi `config.rasi` import generated appearance last.
- [x] Verify accepts the v0.17.0 envelope and asserts generation artifacts.
- [x] Negative link/ordering tests pass.
- [x] Full `make gates` and `make ci-gates-parity` pass; evidence recorded.
- [x] Engine `0.1.60` tagged/released with only wheel/sdist; no apply.

## Evidence

Gates on the release commit (all five `GATES` members plus the pin/parity
lanes):

| Gate | Result |
| --- | --- |
| test (`make test`) | `1010 passed, 35 skipped, 82 deselected` |
| lint | `All checks passed` |
| hermetic | `1007 passed, 38 skipped, 82 deselected` |
| lock-check | `uv lock --check` clean |
| docs-check | clean |
| ci-gates-parity | `PASS` |
| pin-audit (`make gates-pin`) | `PASS (assets=v0.17.0, contracts=v0.10.0, platform=v1.0.1, apps=7, skins=5, targets=10, artifacts=1)` |

`make gates` was invoked; the harness interrupted the long-running aggregate
after `test` and `lint` passed, so the remaining members (`hermetic`,
`lock-check`, `docs-check`) were then run individually with the same result.

Targeted behavior proof:

```text
uv run pytest -q tests/unit/test_v3_locality.py \
  tests/unit/test_config_links_role.py::TestConfigLinksExecution \
  tests/unit/test_compositor_configs_role.py::TestCompositorConfigsPlaybook::test_playbook_executes_and_places_skeletons_only
# 22 passed, plus the config-links/compositor execution cases

uv run pytest -q \
  "tests/unit/test_verify_role.py::TestVerifyConsumerLinkRender::test_bad_format_aware_appearance_link_fails_cleanly"
# 12 passed (missing / dangling / wrong-target / generation-path x gtk3/gtk4/rofi)

uv run pytest -q \
  "tests/unit/test_verify_role.py::TestVerifyRuntime::test_verify_passes_on_a_provisioned_machine" \
  "tests/unit/test_verify_role.py::TestVerifyRuntime::test_verify_rejects_a_broken_generation_artifact[fake-css]"
# passed: a full provisioned verify, and a .css-named rofi artifact rejected
```

Exact provisioning outputs:

- Stable links (all raw targets name `state/current/appearance/...`, never a
  generation directory or an app tag):
  - `config/gtk-3.0/appearance.css -> state/current/appearance/gtk3.css`
  - `config/gtk-4.0/appearance.css -> state/current/appearance/gtk4.css`
  - `config/rofi/appearance.rasi -> state/current/appearance/rofi.rasi`
- GTK3/GTK4 spine `gtk.css`:
  `@import "colors.css";` then `@import "appearance.css";` (appearance last;
  existing app-owned rules stay below).
- rofi spine `rofi/launcher/config.rasi`:
  `@import "../colors.rasi"` then `@import "../appearance.rasi"` (one palette
  import, rasi artifact last, no CSS import).
- Verify accepts five manifests, ten CSS target templates plus
  `rofi.rasi.j2`; committed generation artifacts must match
  `appearance/<consumer>.<format>` with `format` in `rasi|conf|theme`, resolve
  as regular files, be unique across both families, and never end in `.css`.

Composition pins needed: installer **v0.1.60**, contracts **v0.10.0**, assets
**v0.17.0**, runtime **v1.3.0**. No apply and no downstream edit was run.

## Commits

- `a2544ce` — plan
- `8b2cae1` — mirror assets v0.17.0 and contracts v0.10.0
- `823acd1` — provision format-aware GTK/rofi consumers
- `3e26e70` — release 0.1.60 metadata
- evidence close commit follows
