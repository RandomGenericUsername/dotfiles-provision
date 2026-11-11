---
id: REQ-039
title: "Phase 0 hardening for the skin consumer plane (pin-audit + wlogout fallback)"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-039/
branch: ticket/REQ-039-skin-consumer-phase0
---

# Phase 0 hardening for the skin consumer plane

## Requirement

Harden the consumer plane before any runtime/composition cutover:

1. **Pin-audit manifest coverage.** `scripts/pin-audit.py` fails when
   `verify_skins_manifest_names` is not exactly the released five manifests
   (`glass`, `flat`, `paper`, `terminal`, `terminal-host`), or when the
   required skin target set is not the released eight templates (seven AGS
   targets plus wlogout). This stays a structural/pin audit, not a schema
   validator.
2. **wlogout bootstrap fallback.** The provisioning-owned wlogout config spine
   gains an empty (palette-only) `appearance.css` fallback only when no
   appearance file/link exists. An existing stable symlink is preserved.
   `state_links` keeps forcing the real
   `current/appearance/wlogout.css` link when the generation is available, so
   the fallback never survives a seeded run. No runtime artifact is written
   into an app tag; there is no live reload lane.

## Gate strategy

- The pin-audit/tooling change is validated with `make gates-pin` (pin-audit,
  lint, docs-check, CI-gates parity).
- The wlogout fallback is a behavior change, so the release also runs the full
  `make gates` (`test lint hermetic lock-check docs-check`) and
  `make ci-gates-parity`. `make gates-pin` alone is not sufficient for the
  behavior commit.

## Acceptance

- [x] `pin-audit` fails on a missing/extra skin manifest name or target file,
      with regression tests covering the five names and `terminal-host`.
- [x] Fresh wlogout provisioning with no appearance link writes a regular
      fallback `config/wlogout/appearance.css`; it parses as GTK3 CSS.
- [x] An existing stable `appearance.css` symlink is preserved by the fallback
      task (no clobber).
- [x] `state_links` replaces the regular fallback with the
      `current/appearance/wlogout.css` symlink after the seed; no stale
      fallback remains.
- [x] Full `make gates` and `make ci-gates-parity` pass; evidence recorded.
- [x] Engine `0.1.59` tagged/released with only its wheel/sdist; no apply and
      no composition/runtime/app/contract edits.

## Evidence

Full gates on the REQ-039 worktree at `ff81d42` (clean tree; the following
evidence-only commit changes no code):

| Gate | Result |
| --- | --- |
| `make test` / test | `1031 passed, 3 skipped, 67 deselected` |
| `make lint` / lint | `All checks passed` |
| `make hermetic` / hermetic | `996 passed, 38 skipped, 67 deselected` |
| `make lock-check` / lock-check | clean |
| `make docs-check` / docs-check | clean |
| `make ci-gates-parity` | `PASS` |

Pin-audit portion (`make gates-pin` before the behavior merge):

```text
pin-audit: PASS (assets=v0.16.0, contracts=v0.9.0, platform=v1.0.1, apps=7, skins=5, targets=8)
python3 scripts/ci-gates-parity.py
PASS gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test'] jobs=[...]
```

Targeted behavior proof (assets corpus provided):

```bash
uv run pytest -q tests/unit/test_verify_role.py::TestVerifySkinPlane \
  tests/unit/test_pin_audit.py tests/unit/test_wlogout_config_role.py \
  tests/unit/test_v3_locality.py
# 63 passed
```

Exact fallback behavior:

- Fresh no-link run: the role's stat (`follow: false`) sees no path, then
  `copy force: false` writes an empty regular
  `<install>/config/wlogout/appearance.css`; the system GTK3 `CssProvider`
  probe parses it with zero parsing errors.
- Existing stable symlink: the stat sees the link itself and the
  create-if-absent task is skipped; the symlink target and content are
  unchanged.
- Seeded run: `state_links` (`file state: link force: true`) replaces the
  regular fallback with
  `$XDG_STATE_HOME/dotfiles/current/appearance/wlogout.css`; a test asserts
  the fallback content is gone and the raw link target is correct.
- No runtime artifact or app-tag write; no live-reload lane.

Exact pin-audit behavior:

- `verify_skins_manifest_names` must be exactly
  `glass, flat, paper, terminal, terminal-host`.
- `verify_skins_template_files` must be exactly the eight released targets:
  the seven AGS templates plus `wlogout.gtk.css.j2`.
- Regression tests fail on a missing `terminal-host`, an extra manifest, a
  missing wlogout target, and an extra target.

Composition pin needed: `dotfiles-provision` installer **v0.1.59**. No
composition/runtime/app/contract file is edited here and `apply` is not run.

## Commits

- `65d4fda` — plan
- `c08d53f` — pin-audit skin manifest/target coverage
- `02bd7b2` — wlogout bootstrap appearance fallback
- `786384e` — fallback link replacement + terminal-host fixture tests
- `82a3638` — expect all five released skin manifests
- `ff81d42` — release 0.1.59 metadata
- evidence close commit follows
