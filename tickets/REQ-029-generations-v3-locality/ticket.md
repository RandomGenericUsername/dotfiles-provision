---
id: REQ-029
title: "Deploy v3 state locality: immutable app tags and stable consumer links"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-029/
branch: ticket/REQ-029-generations-v3-locality
---

# Deploy v3 state locality: immutable app tags and stable consumer links

## Requirement

Generations v3 (`dotfiles-v3/docs/107-generations-v3.md` §2.7, contracts
`generations.md` v0.8.0 §6) moves every runtime write under
`$XDG_STATE_HOME/dotfiles/` and makes `<install>/apps/<installDir>/<tag>` an
immutable app tag. The engine must stop expecting runtime files inside a tag or
inside an app's config spine link, provide provisioning-owned stable links for
the non-runtime palette consumers (`gtk-3.0`, `gtk-4.0`, `rofi`, `btop`) that
resolve through `current/palette/...`, and verify the generation manifest plus
the immutability boundary. App runtime sheets are read by the app from
`state/current/appearance/<configDir>.css`; provisioning never copies or links
them through a tag.

Fresh-install absence stays tolerated: provisioning creates only stable links,
and verify rejects a runtime artifact only when one is actually present.

## Acceptance

- [ ] `state_links` role creates the four provisioning-owned stable consumer
      links in `<install>/config/{gtk-3.0,gtk-4.0,rofi,btop}` pointing at
      `$XDG_STATE_HOME/dotfiles/current/palette/...`; it never writes through
      an AGS app spine link or into a tag.
- [ ] `wlogout` reads the palette directly from
      `state/current/palette/colors.gtk.css`; no `config/ags/colors.css`
      runtime pointer is required.
- [ ] `runtime-seed` asserts a committed v3 generation
      (`current/manifest.json`, `version: 3`, hash == current target) instead of
      v2 consumer links under the install spine.
- [ ] `ags_apps_units` removes stale runtime artifacts
      (`appearance.css`, `skin.css`, `skin.json`, `tokens.json`, `colors*`)
      from an existing tag on reinstall/rollback and verifies none remain.
- [ ] `verify` asserts the generation manifest/current hash and
      `current/appearance/<configDir>.css` targets when present, verifies the
      stable consumer links resolve through `current/palette/`, and fails when
      a runtime artifact is planted in any app tag.
- [ ] The engine expects contracts `v0.8.0` where it validates the generation
      schema/PIN, and the fixture suite carries the vendored schema/PIN.
- [ ] Role tests cover immutable app installs, stable consumer links,
      absent-state tolerance and generation-manifest verification.
- [ ] `make gates` and `make ci-gates-parity` pass; engine version + CHANGELOG,
      annotated tag, fast-forward merge, push `main` + tag; no apply.

## Non-goals

- No composition pin, app tag, runtime pin or live host is changed here.
- No app code is copied into a writable directory; no second pointer or
  v2 consumer-link fallback is added.
