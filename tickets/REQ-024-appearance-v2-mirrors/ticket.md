---
id: REQ-024
title: "Mirror the dotfiles-v3 appearance v2 tuple in the engine"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-024/
branch: ticket/REQ-024-appearance-v2-mirrors
---

# Mirror the dotfiles-v3 appearance v2 tuple in the engine

## Requirement

Composition `dotfiles-v3` now declares the appearance-v2 program tuple:
`ags-platform: v0.9.0`, `contracts: v0.7.0` and `dotfiles-assets: v0.12.2`
(runtime is `v0.9.2` and is derived from `cli_tools_tags`, not mirrored here).
The engine still pins platform `v0.8.0` and assets `v0.11.0`, and its skins
verify plane still describes the frozen v1 manifests. A live v2 deploy would
therefore install v1 platform/assets, and `dotfiles-v3` `make deploy-coverage`
cannot resolve the tuple.

The engine must mirror the platform/assets tags, mirror the contracts PIN at
`v0.7.0`, accept the assets `skins` schema major 2 on fetch/verify, and verify
the deployed v2 skin plane: `schemaVersion = 2` manifests with nested
`groups.surface/state/type/ink/layout` (plus mode overrides), seven
`<configDir>.gtk.css.j2` templates, the resolved `tokens.json` shape
`{version: 2, surface, state, type, ink, layout}`, and the vendored appearance
schemas' sha256 values. The v1-only checks (`schema_major`, the 24-token flat
set, `hairline-w` as a flat token) must go. Runtime-owned skin pointers stay
optional when absent.

## Acceptance

- [ ] `ags_platform_version` and `verify_ags_platform_version` are `v0.9.0`
      and still derive unit dir/pin/shortcut from the one var.
- [ ] Every `*_assets_pinned_tag` mirror (all nine role mirrors), the
      composition fixture `assets.yaml` (tag + checkout sources) and
      `program-tuple.yaml` (`ags-platform`/`contracts`/`dotfiles-assets`) are
      `v0.12.2`/`v0.9.0`/`v0.7.0`/`v0.12.2`.
- [ ] The assets/verify `skins` schema support window is 2, so the v0.12.2
      `skins/schema.json` fetch passes.
- [ ] Verify asserts v2 manifests (`schemaVersion = 2`, nested groups, optional
      mode overrides), the resolved `tokens.json` contract shape, all seven
      templates and v2 placeholder paths, and the contracts PIN `v0.7.0` with
      the appearance schema sha256 values.
- [ ] v1-only checks are removed: no `schema_major = 1`, 24-token flat set or
      flat `hairline-w` requirement remains in the skins plane.
- [ ] Runtime `skin.css`/`skin.json` pointer checks still tolerate absent
      pointers and reject a present non-`current/` pointer.
- [ ] Tests/fixtures hardcoding `v0.8.0`/`v0.11.0` move to
      `v0.9.0`/`v0.12.2`; new tests prove a valid v2 plane passes and a
      tampered v2 manifest/template fails.
- [ ] `make gates`, `make ci-gates-parity` and the local-corpus template-vars
      parity against `/home/inumaki/Development/dotfiles/dotfiles-assets` pass.
- [ ] Engine `0.1.38` + CHANGELOG; annotated tag `v0.1.38` after the
      fast-forward merge; push `main` and the tag; no apply.

## Evidence / Verify

Worktree `.worktrees/REQ-024/`, branch
`ticket/REQ-024-appearance-v2-mirrors`.

(Filled in by the implementation and evidence commits.)
