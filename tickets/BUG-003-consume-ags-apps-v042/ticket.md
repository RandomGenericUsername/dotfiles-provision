---
id: BUG-003
title: "Consume ags-apps v0.4.2 (color thumbnails) + release v0.1.12"
kind: bug
status: done
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
- [x] Merge to `main`; annotated tag `v0.1.12`; push; GH release carries the
      sdist + wheel (tag CI).
- [x] `dotfiles-v3` `installer.pin` → `v0.1.12`; `verify` on the host passes
      with `--expected-engine-tag v0.1.12`.

## Closeout

| Claim | Command | Result |
| --- | --- | --- |
| Engine gates | `make gates` (worktree) | exit 0 — test 983 passed/3 skipped/54 deselected; hermetic 951/35/54; ruff clean; `uv lock --check` resolved 33; docs-check included |
| Merge + tag | `git log`/`git tag` | `0e6865e` merge on `main`; annotated `v0.1.12` |
| Tag CI | `gh run view 40257973984 --repo …` | `completed/success` (4m55s); release published |
| Release assets | `gh release view v0.1.12 --json assets` | `dotfiles_provision-0.1.12-py3-none-any.whl`, `dotfiles_provision-0.1.12.tar.gz` |
| Composition pin | `dotfiles-v3 @ c3ecf1f5` (pushed) | `installer.pin` → `v0.1.12`; its `make gates` exit 0; pin-set table reads `installer dotfiles-provision v0.1.12` |
| Engine installed | `uv tool install --force "git+…@v0.1.12"` | 0.1.11 → 0.1.12, executable replaced |
| Full plan blocked (expected) | `make provision ARGS="plan"` | fails at the first become play with `sudo: a password is required`; packages bootstrap is the only sudo scope and needs an interactive password |
| ags-apps unit deployed | driver `rollout-BUG-003-agsapps.py` (uses the installed v0.1.12 package's own EngineSettings→AnsibleExecutor→ProvisionMachineUseCase chain, seam = dotfiles-v3 composition) on the user-scoped `ags-apps.yaml` play | success: True; ok=29 changed=14; clone+pin record + all seven live links repointed to `ags-apps/v0.4.2` |
| follow-up | same driver on `compositor-configs.yaml` (regenerates `icons.json` through the fresh unit links — a full bootstrap runs it in role order after ags_apps; a staged single-playbook roll-out leaves generated artifacts behind in a NEW unit dir) | success; `[changed] Generate capture AGS JSON manifest` |
| Host verify | `make provision ARGS="verify --expected-engine-tag v0.1.12"` (from `dotfiles-v3`) | exit 0; ok=186 failed=0; engine v0.1.12 handshake ok; all ags-apps unit + live-link assertions ok (incl. wallpaper-selector v0.4.2) |

Roll-out note: the FIRST verify run failed at
`Assert compositor configs and skeletons are present with correct types`
(`config/ags-capture/icons.json` absent — v0.4.2 is a FRESH unit clone; the
generated `icons.json` from the previous v0.1.11-era tree does not carry over
because generated artifacts live in the unit tree). Consumed state was fixed by
running the sibling `compositor-configs.yaml` user-scoped playbook (the
aggregate's normal order). No engine change needed; recorded here so the next
staged unit bump runs the follower playbook before verify.
