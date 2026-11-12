---
id: REQ-044
title: "Mirror the parity app releases in the engine final inventory (bar v0.6.4 note v0.6.3 sound-panel)"
kind: requirement
status: done
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

- [x] Every app inventory mirror carries the parity tags; contracts/assets/
      platform pins are unchanged.
- [x] `make gates-pin`, targeted app inventory/pin tests, docs-check, assets
      parity and the build/wheel checks pass.
- [x] The superseded `v0.1.54`/`v0.1.55` note is present and explicit.
- [x] Engine `0.1.64` is tagged/released with only wheel/sdist; no apply.

## Evidence

Pin-only lane per the ticket instruction: `make gates-pin` instead of full
`make gates` (no behavior/schema change).

| Gate | Result |
| --- | --- |
| `make gates-pin` | PASS (rc `0`; pin-audit + lint + docs-check + ci-gates-parity) |
| pin-audit | `PASS (assets=v0.19.0, contracts=v0.12.0, platform=v1.1.0, apps=7, skins=5, targets=10, artifacts=2)` |
| lint | `All checks passed!` |
| docs-check | PASS (including `SUPERSEDED.md` added; README/CHANGELOG/LICENSE/AGENTS/CLAUDE intact) |
| ci-gates-parity | `PASS gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test']` |
| targeted tests | `pytest ...TestAllStandaloneFixture ...test_pin_audit.py ...test_ags_units_supervision.py` → `26 passed` |
| lock-check | `uv lock --check` clean |
| assets-parity | `PASS assets-parity: 10 tests executed, 0 skipped` (`dotfiles-assets @ v0.19.0`) |
| build | `dotfiles_provision-0.1.64.tar.gz` + `dotfiles_provision-0.1.64-py3-none-any.whl`; `check-wheel-contents.py` PASS |

Exact engine app inventory after this release:

```text
bar                  v0.6.4   (v0.6.3 is the sound-panel release)
notifications        v0.5.2
capture              v0.7.2
clipboard            v0.6.2
wallpaper-selector   v0.5.2
icme                 v0.5.2
btop-theme-studio    v0.5.2
```

Unchanged engine mirrors: contracts **v0.12.0**, assets **v0.19.0**,
platform **v1.1.0**. Runtime remains composition-owned (no engine pin).

Build artifact digests:

```text
8454adaf062e6134f4c22ec697dc735796dcfa84b430276157927b6f3ad257dd  dotfiles_provision-0.1.64-py3-none-any.whl
59802f611a998cbf40f2ff33bff41a49e130b191cbf52828d1e6caab1857e3cf  dotfiles_provision-0.1.64.tar.gz
```

Superseded releases note: `SUPERSEDED.md` (repo root). It states that engine
tags `v0.1.54` and `v0.1.55` are immutable mistakes that must not be used, and
that `v0.1.56+`/`v0.1.64` are authoritative. Documentation only.

Composition pins needed downstream (read-only note; no downstream edits):

- dotfiles-provision installer **v0.1.64**
- app tags: bar **v0.6.4**, notifications **v0.5.2**, capture **v0.7.2**,
  clipboard **v0.6.2**, wallpaper-selector **v0.5.2**, icme **v0.5.2**,
  btop-theme-studio **v0.5.2**
- contracts **v0.12.0**, assets **v0.19.0**, ags-platform **v1.1.0** unchanged.

No apply, no downstream edits, no runtime/assets/composition/app edits and no
live state writes.

## Commits

- `2afd178` — plan commit (ticket + INDEX)
- `45086f3` — pin the parity app releases + `SUPERSEDED.md`
- `107c678` — release `0.1.64` metadata (version, lock, CHANGELOG)
- evidence close commit follows; tag `v0.1.64`
