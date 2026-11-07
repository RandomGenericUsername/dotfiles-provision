---
id: BUG-010
title: "v3 cutover fails an idempotent seed and leaves runtime artifacts in historical app tags"
kind: bug
status: in-progress
lane: 2
severity: high
links:
  openspec: none
  bmad: none
worktree: .worktrees/BUG-010/
branch: ticket/BUG-010-v3-seed-idempotent-tag-sweep
repro: "Run the v3 cutover apply twice without changing the intended state. The second runtime-seed run returns rc=0, leaves current/manifest.json unchanged, and the seed assertion 'Assert the seed produced fresh generation state' fails because state_advanced is false. Separately, on a host whose old app tags were written by a v1/v2 runtime, verify fails 'Assert no runtime artifact exists inside an immutable app tag' for artifacts under <install>/apps/<installDir>/<tag>/ that are not the currently pinned tag."
observed: "On an idempotent apply the seed reports rc=0, state_advanced=False and current/manifest.json exists, so 'Assert the seed produced fresh generation state' fails with 'runtime seed did not produce a fresh generation manifest'. The v0.1.43 migration sweep only removes artifacts from each app's CURRENT tag in _one.yml; historical tags under the same installDir keep appearance.css/skin.css/skin.json/colors.css/tokens.json/colors.*, so the verify find still matches them."
expected: "An idempotent seed is success: rc=0 with an existing current/manifest.json must pass regardless of whether the generation advanced, and the existing v3 manifest/current-target assertions still run. A tolerated rc=1 must still require a fresh/changed valid manifest; rc>1 fails. A migration sweep before verify must remove only the documented runtime-artifact allowlist from every installed app tag directory (<install>/apps/<installDir>/<tag>/), including historical tags, while leaving app source and .git untouched; the current-tag immutability assert stays."
---

# BUG-010 — v3 cutover idempotent seed + historical tag sweep

## Root cause

Two final v3 cutover edges:

1. `runtime-seed` treats "the generation advanced" as required for every
   successful seed. A second apply with the same intended state derives the
   same generation, returns rc=0 and leaves `current/manifest.json` untouched,
   so `runtime_seed_state_advanced` is false and the assertion fails. rc=0 is
   already success; only a tolerated rc=1 needs fresh state.
2. The v0.1.43 migration sweep is per-app (`ags_apps_units/tasks/_one.yml`) and
   therefore only cleans `<install>/apps/<installDir>/<current tag>/`.
   Historical tags written by a v1/v2 runtime keep the same runtime-owned
   artifacts under `<install>/apps/<installDir>/<old tag>/`, which `verify`
   scans recursively and rejects.

## Fix

- `runtime-seed`: change the postcondition to accept rc=0 whenever the
  committed `current/manifest.json` exists (and parses; the existing v3
  generation assertion already proves its `generationHash` equals the current
  target basename). Accept rc=1 only when the manifest exists AND advanced.
  Keep `rc not in [0, 1]` failing at the command task and at the assert.
- `ags_apps_units`: add a migration sweep (`_sweep_tags.yml`) that enumerates
  every installed app tag directory under `<install>/apps/<installDir>/<tag>/`
  and removes the documented runtime-artifact allowlist. Deletion is limited to
  files/symlinks with an allowlisted basename; real directories, app source and
  `.git` are never touched. The per-app current-tag sweep and its
  immutability assert stay.
- The sweep runs inside `ags_apps_units`, before `verify` in bootstrap order.

## Acceptance

- [ ] Idempotent seed (rc=0, unchanged valid manifest) passes.
- [ ] rc=1 with a fresh valid manifest passes; rc=1 without a manifest fails;
      rc>1 fails.
- [ ] The sweep removes runtime artifacts from historical tags and leaves app
      source and `.git` unchanged.
- [ ] Verify passes after the sweep (its recursive find matches zero); the
      current tag is clean and its immutability assert remains.
- [ ] `make gates`, `make ci-gates-parity` and targeted runtime-seed/verify/
      locality suites pass.
- [ ] Engine `0.1.46` + CHANGELOG, annotated tag `v0.1.46` after the
      fast-forward merge; push `main` and the tag; no apply.

## Non-goals

- No live apply is run here.
- No composition, runtime, assets or app tag is changed.

## Allowlist (documented)

Runtime-owned basenames swept from each tag (glob `colors*` covers the retired
palette-pointer family):

`appearance.css`, `skin.css`, `skin.json`, `tokens.json`, `colors*`

Only files and symlinks with these basenames are removed. A directory with a
matching name, any other file, `.git`, and every app source file are untouched.
