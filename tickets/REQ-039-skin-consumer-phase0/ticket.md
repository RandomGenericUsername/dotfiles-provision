---
id: REQ-039
title: "Phase 0 hardening for the skin consumer plane (pin-audit + wlogout fallback)"
kind: requirement
status: in-progress
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

- [ ] `pin-audit` fails on a missing/extra skin manifest name or target file,
      with regression tests covering the five names and `terminal-host`.
- [ ] Fresh wlogout provisioning with no appearance link writes a regular
      fallback `config/wlogout/appearance.css`; it parses as GTK3 CSS.
- [ ] An existing stable `appearance.css` symlink is preserved by the fallback
      task (no clobber).
- [ ] `state_links` replaces the regular fallback with the
      `current/appearance/wlogout.css` symlink after the seed; no stale
      fallback remains.
- [ ] Full `make gates` and `make ci-gates-parity` pass; evidence recorded.
- [ ] Engine `0.1.59` tagged/released with only its wheel/sdist; no apply and
      no composition/runtime/app/contract edits.
