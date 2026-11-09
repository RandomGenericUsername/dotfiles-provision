---
id: REQ-033
title: "Provision the wlogout appearance consumer link (SKIN-WLOGOUT slice)"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-033/
branch: ticket/REQ-033-skin-wlogout
---

# Provision the wlogout appearance consumer link (SKIN-WLOGOUT slice)

## Requirement

`dotfiles-assets` v0.14.0 ships the wlogout paint/rhythm template
(`skins/templates/wlogout.gtk.css.j2`) and its static
`templates/wlogout/style.css.tpl` imports the generated `appearance.css`
**last**. The v3 runtime publishes `state/current/appearance/wlogout.css` and
a matching generation-manifest target. Provisioning must join the two with its
own stable consumer link, exactly as it already does for the palette consumers:

```text
<install>/config/wlogout/appearance.css
  -> $XDG_STATE_HOME/dotfiles/current/appearance/wlogout.css
```

The link names the one `current` commit pointer, never a generation-specific
path and never an `<install>/apps/<tag>` path. It is created even when a fresh
state root has no generation yet, and asserted to resolve once a generation is
committed. `verify` re-asserts the raw target, resolution and the absence of a
generation/app-tag route.

Assets moves to **v0.14.0** in the engine mirrors and composition fixtures;
`contracts: v0.8.0` and `ags-platform: v1.0.1` stay unchanged. This slice does
not edit `dotfiles-v3`, the runtime, any app repo or live host state, and it
does not run `apply`.

Criteria: `W-2.5`–`W-2.8` in
`dotfiles-v3/docs/108-non-ags-skin-consumers.md`; epic `SKIN-CONSUMERS`.

## Acceptance

- [ ] `state_links` owns a stable wlogout link
      `config/wlogout/appearance.css -> state/current/appearance/wlogout.css`
      in the same consumer list as the palette links, using the existing
      create-then-assert-once-seeded flow. No generation path and no app tag.
- [ ] `verify` asserts the raw `stat.lnk_target` is exactly
      `current/appearance/wlogout.css`, the followed link is a regular file,
      and the target contains neither `generations` nor an app-tag route.
- [ ] `wlogout_config` still renders the assets v0.14.0 static style and the
      rendered sheet imports `appearance.css` **last**; wallpaper, icons,
      layout IDs, transitions and the palette import remain app-owned. No new
      render variable is required by the released template.
- [ ] Every engine `*_assets_pinned_tag` mirror, the composition fixture
      `assets.yaml` (tag + four checkout sources), the fixture
      `program-tuple.yaml`, and hardcoded pin assertions move to
      **v0.14.0**; `contracts: v0.8.0` and `ags-platform: v1.0.1` do not move.
- [ ] `test_v3_locality.py`, `test_verify_role.py` and
      `test_wlogout_config_role.py` cover the positive link/order and the
      negative missing, dangling and wrong-target cases.
- [ ] Targeted tests, `make gates` and `make ci-gates-parity` pass on the
      ticket branch.
- [ ] Engine `0.1.50` + CHANGELOG, annotated tag `v0.1.50` after the
      fast-forward merge; push `main` and the tag; the GitHub Release carries
      only the 0.1.50 sdist and wheel; no apply.

## Non-goals

- No `dotfiles-v3` composition pin edit, runtime code, app code, contract
  schema change or live host change.
- No wlogout live-reload lane; the documented semantics stay "next launch".
- No new pointer routed through a generation directory or an app tag.
- No layout/icons/wallpaper/transition token moves into the generated sheet.

## Evidence / Verify

Worktree `.worktrees/REQ-033/`, branch `ticket/REQ-033-skin-wlogout`.
Commits: plan (this file + INDEX), implementation/release metadata, then
evidence. Annotated tag `v0.1.50` on the fast-forward merge commit; no apply.

Evidence is recorded in this ticket after the gates complete.
