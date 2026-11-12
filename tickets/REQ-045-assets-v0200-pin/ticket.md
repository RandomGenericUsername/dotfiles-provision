---
id: REQ-045
title: "Mirror dotfiles-assets v0.20.0 (sound panel paint)"
kind: requirement
status: done
lane: 1
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-045/
branch: ticket/REQ-045-assets-v0200-pin
---

# Mirror dotfiles-assets v0.20.0

## Requirement

Pin-only lane. Move the engine's assets mirror from v0.19.0 to **v0.20.0**
(REQ-028 sound-panel paint in `skins/templates/ags.gtk.css.j2`). Contracts
`v0.12.0`, platform `v1.1.0`, runtime ownership and the app inventory
(bar `v0.6.4`) stay unchanged.

1. Every `*_assets_pinned_tag` mirror plus `verify_assets_pinned_tag` moves to
   `v0.20.0`; the v0.20.0 schema/template envelope is unchanged (five
   manifests, twelve templates, rofi/rasi + kitty/conf).
2. The composition fixture (`assets.yaml`, `program-tuple.yaml`) and the
   hardcoded pin assertions move to `v0.20.0`.
3. `scripts/pin-audit.py` expected plane comment names v0.20.0.
4. `pyproject.toml` / `uv.lock` release metadata `0.1.65`; CHANGELOG entry.
5. Gates: `make gates-pin`, targeted asset/pin tests, `make assets-parity`,
   `make build`; no apply.
6. Tag/push `v0.1.65`.

## Acceptance

- [x] Every assets mirror and fixture names v0.20.0; the app/platform/contracts
      pins are unchanged.
- [x] `make gates-pin`, targeted tests, `assets-parity` and the wheel/sdist
      build pass.
- [x] `v0.1.65` is tagged/pushed; no apply.

## Evidence

- Worktree `.worktrees/REQ-045/`, branch
  `ticket/REQ-045-assets-v0200-pin`, based on `d8ec793` (v0.1.64).

| Gate | Result |
| --- | --- |
| `make gates-pin` | PASS (rc 0; pin-audit assets=v0.20.0, ruff, docs-check, ci-gates-parity) |
| `make assets-parity` | PASS on the released assets v0.20.0 clone (10 tests, 0 skipped) |
| `make build` | PASS: `dotfiles_provision-0.1.65` sdist + wheel; wheel contents include the Ansible tree |
| `tests/unit/test_assets_role.py` | 38 passed |
| `tests/unit/test_display_manager_role.py` | 21 passed, 6 skipped |
| `tests/unit/adapters/test_yaml_manifest_reader.py` | 66 passed |
| full `make test` / selected `TestVerify*` | timed out in this environment before completing; pin-only lane uses `gates-pin` per the Makefile contract. No behavior/schema change. |
