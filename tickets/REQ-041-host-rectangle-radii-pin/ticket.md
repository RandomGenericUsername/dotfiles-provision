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

## Evidence

Gate choice: **`make gates-pin`** (pin-only lane: pin-audit + lint +
docs-check + ci-gates-parity). No behavior/schema change landed, so the full
`make gates` suite was not required.

| Gate | Result |
| --- | --- |
| pin-audit (`make gates-pin`) | `PASS (assets=v0.18.0, contracts=v0.11.0, platform=v1.0.1, apps=7, skins=5, targets=10, artifacts=1)` |
| lint | `All checks passed!` |
| docs-check | clean |
| ci-gates-parity | `PASS gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test']` |
| lock-check | `uv lock --check` clean |
| build | `dotfiles_provision-0.1.61.tar.gz` + `dotfiles_provision-0.1.61-py3-none-any.whl`; `check-wheel-contents.py` PASS |

Targeted tests:

```text
pytest tests/unit/test_v3_locality.py tests/unit/test_pin_audit.py
       tests/unit/test_verify_role.py::TestVerifyVars
       tests/unit/test_verify_role.py::TestVerifyAssetsSchemaWindow
# 85 passed

pytest tests/unit/test_verify_role.py::TestVerifySkinPlane
# 14 passed in 192.97s (the ansible-backed skin execution probes)

pytest tests/unit/test_display_manager_role.py
       tests/unit/test_ags_apps_units_role.py
       tests/unit/test_runtime_seed_playbook.py
       tests/unit/adapters/test_yaml_manifest_reader.py
       -k "pin or assets or generation or tuple or manifest or mirror"
# 74 passed, 1 skipped
```

Exact pins:

- installer **v0.1.61**, contracts **v0.11.0**, assets **v0.18.0**,
  runtime **v1.3.0**, platform **v1.0.1**
- vendored generation schema sha256
  `e3fe10bd27cd102056af2249a9631c6289a0a41cb35aca2a79bff63c7e97fd53`
- skin envelope unchanged: 5 manifests (`glass`, `flat`, `paper`, `terminal`,
  `terminal-host`), 11 templates (10 `<configDir>.gtk.css.j2` CSS targets +
  `rofi.rasi.j2` artifact), 10 targets, 1 artifact.

Host delegation recorded by contracts v0.11.0: `surface.panel.radius`,
`surface.panel.border-width`, `surface.card.radius`,
`surface.control.radius`, `surface.cell.radius`; `surface.pill.radius` is
explicit and rejected as a host default.

No apply, no runtime/assets/composition/app edits and no live state writes.

## Commits

- `3f49c1f` — plan
- `e0e153a` — mirror assets v0.18.0 and contracts v0.11.0
- `1050d70` — release 0.1.61 metadata
- evidence close commit follows; tag `v0.1.61`

## Acceptance

- [x] Engine pins and fixtures mirror assets `v0.18.0` / contracts `v0.11.0`.
- [x] Contracts `v0.11.0` generation schema and rectangle fixtures are vendored.
- [x] Pin audit stays fail-closed with the unchanged skin envelope.
- [x] `make gates-pin` and targeted tests pass; gate choice recorded.
- [x] Engine `0.1.61` tagged/released with only wheel/sdist; no apply.
