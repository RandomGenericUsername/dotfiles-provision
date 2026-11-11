---
id: REQ-042
title: "Mirror dotfiles-assets v0.18.1 (rofi generated appearance last)"
kind: requirement
status: done
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

- [x] Engine pins and fixtures mirror assets `v0.18.1`; contracts stay `v0.11.0`.
- [x] Pin audit keeps the same fail-closed skin/target/artifact sets.
- [x] `make gates-pin` and targeted assets/verify/pin tests pass; docs-check,
      parity and build/wheel check pass.
- [x] Engine `0.1.62` tagged/released with only wheel/sdist; no apply.

## Evidence

Gate choice: **`make gates-pin`** (pin-only lane: pin-audit + lint +
docs-check + ci-gates-parity). No behavior/schema change landed, so the full
`make gates` suite was not required. `make assets-parity` was also run against
the real pinned corpus.

| Gate | Result |
| --- | --- |
| pin-audit (`make gates-pin`) | `PASS (assets=v0.18.1, contracts=v0.11.0, platform=v1.0.1, apps=7, skins=5, targets=10, artifacts=1)` |
| lint | `All checks passed!` |
| docs-check | clean |
| ci-gates-parity | `PASS gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test']` |
| assets-parity | `PASS assets-parity: 10 tests executed, 0 skipped` (`dotfiles-assets @ v0.18.1`) |
| lock-check | `uv lock --check` clean |
| build | `dotfiles_provision-0.1.62.tar.gz` + `dotfiles_provision-0.1.62-py3-none-any.whl`; `check-wheel-contents.py` PASS |

Targeted tests:

```text
pytest tests/unit/test_v3_locality.py tests/unit/test_pin_audit.py
       tests/unit/test_verify_role.py::TestVerifyVars
       tests/unit/test_verify_role.py::TestVerifyAssetsSchemaWindow
       tests/unit/test_display_manager_role.py
       tests/unit/test_ags_apps_units_role.py
       tests/unit/test_runtime_seed_playbook.py
       tests/unit/adapters/test_yaml_manifest_reader.py
       -k "pin or assets or generation or tuple or manifest or mirror"
# 150 passed, 1 skipped, 92 deselected in 14.37s

pytest tests/unit/test_verify_role.py::TestVerifySkinPlane
# 14 passed in 213.00s
```

Build artifacts:

```text
db25c81d... dotfiles_provision-0.1.62-py3-none-any.whl
ce217e97... dotfiles_provision-0.1.62.tar.gz
```

Exact engine pins:

- installer **v0.1.62**, assets **v0.18.1**, contracts **v0.11.0**,
  platform **v1.0.1**, runtime fixture **v0.4.1**, tpr **v0.4.0**
- apps: bar **v0.6.1**, notifications **v0.5.1**, capture **v0.7.1**,
  clipboard **v0.6.1**, wallpaper-selector/icme/btop-theme-studio **v0.5.1**
- skin envelope unchanged: 5 manifests (`glass`, `flat`, `paper`, `terminal`,
  `terminal-host`), 11 templates (10 `<configDir>.gtk.css.j2` CSS targets +
  `rofi.rasi.j2` artifact), 10 targets, 1 artifact.
- contracts fixtures stay at `v0.11.0`; no contracts file changed.

Assets `v0.18.1` only fixes the static rofi launcher import order so the
generated `appearance.rasi` loads last; the engine re-pins the corpus and does
not change its own render/verify behavior.

Composition installer pin (read-only check, no downstream edit):
`dotfiles-v3/dotfiles/provisioning/installer.pin` is **v0.1.61**; it is not
bumped by this ticket.

No apply, no runtime/assets/composition/app edits and no live state writes.

## Commits

- plan commit — ticket + INDEX
- `38ecb76` — mirror assets `v0.18.1` in engine pins and fixtures
- `6f200f8` — release `0.1.62` metadata
- evidence close commit follows; tag `v0.1.62`
