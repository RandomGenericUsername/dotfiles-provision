---
id: BUG-003
title: "Consume ags-apps v0.4.2 (color thumbnails) + release v0.1.12"
kind: bug
status: in-progress
severity: low
lane: direct
links:
  openspec: none
  bmad: none
worktree: .worktrees/BUG-003/
branch: ticket/BUG-003-consume-ags-apps-v042
observed: "ags-apps v0.4.2 exists (ags-apps BUG-001: wallpaper-selector thumbnails rendered grayscale for every PNG because gdk-pixbuf's JPEG writer mishandles RGBA buffers; fix = flatten to RGB before save + v2 cache bump), but the engine still installs v0.4.1"
expected: "ags_apps_version + the verify mirror advance to v0.4.2; engine v0.1.12 tagged, released, consumed by dotfiles-v3 installer.pin; a real provision verify on the host passes"
---

# BUG-003 — Consume ags-apps v0.4.2 (color thumbnails) + release v0.1.12

## Context

ags-apps `BUG-001` (branch `ticket/BUG-001-grayscale-thumbs`, merged `49adc30`,
tag `v0.4.2`, pushed): the wallpaper-selector's disk-thumbnail path saved
RGBA-derived pixbufs through gdk-pixbuf's JPEG writer, which desaturated every
4-channel buffer (sat 0.0 for all 40 spine PNGs; 3-channel `.jpg` sources saved
correctly). Fix: `flattenToRGB()` composite onto an opaque 3-channel pixbuf over
black before `savev("jpeg")`, plus a `CACHE_VER = "v2"` entry-name bump so the
poisoned v1 cache entries (keyed by stats that never change) are bypassed and
regenerated. Gates: typecheck 0 errors, tests + drift green.

The engine pin (`ags_apps_version`, `ansible/roles/ags_apps/vars/main.yml:102`)
and the hand-maintained verify mirror
(`verify_ags_apps_version`, `ansible/roles/verify/vars/main.yml:686`) must move
together; the parity test
`tests/unit/test_verify_role.py::TestVerifyAgsAppsPinMirror` locks the pair.

## Done-when

- [x] `ags_apps_version: v0.4.2` and `verify_ags_apps_version: v0.4.2`.
- [x] `pyproject.toml` version `0.1.12`, `src/provisioning/__init__.py`
      `__version__` re-aligned (it had drifted to `0.1.6` since the v0.1.9
      manual edit — importlib.metadata is the CLI's source but the module var
      should not lie), `uv.lock` self-version refreshed via `uv lock`,
      CHANGELOG entry.
- [x] `make gates` green in the worktree.
- [ ] Merge to `main`; annotated tag `v0.1.12`; push; GH release carries the
      sdist + wheel (tag CI).
- [ ] `dotfiles-v3` `installer.pin` → `v0.1.12`; `verify` on the host passes
      with `--expected-engine-tag v0.1.12`.

## Closeout

(appended below on completion)
