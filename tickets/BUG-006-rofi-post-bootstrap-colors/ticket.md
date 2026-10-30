---
id: BUG-006
title: "Rofi cannot launch after bootstrap until the first wallpaper set creates colors.rasi"
kind: bug
status: done
lane: 2
severity: high
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-013/
branch: ticket/REQ-013-bootstrap-producer-and-rofi
repro: "Fresh bootstrap, then launch rofi before a wallpaper set has created ~/.config/rofi/colors.rasi; rofi exits with a theme parse error. Removing the symlink reproduces it on the live host."
observed: "2026-10-29 after the tpr/bootstrap cutover the user launched rofi and it failed; no screenshot was captured. The runtime-generated consumer symlink ~/.config/rofi/colors.rasi was recreated at 17:58:30 by a later wallpaper set, after which rofi works. Controlled repro: with the symlink removed, rofi reports `Failed to open theme: .../colors.rasi`, `No such file or directory`, and unresolved color01/color04/background/foreground variables; with it restored, rofi opens (timeout 124, empty stderr)."
expected: "After `bootstrap.sh` returns, every provisioned launcher exposes a usable palette: rofi opens with no theme parse error, even before the user manually switches wallpaper."
---

# BUG-006 — Rofi cannot launch after bootstrap until the first wallpaper set

## Summary

The provisioned rofi launcher hard-imports the runtime-generated palette:

```rasi
# ~/.config/rofi/launcher/config.rasi:1
@import "../colors.rasi"
```

`~/.config/rofi/colors.rasi` is not a provisioning-owned file. It is a runtime
consumer symlink created by `dotfiles-runtime wallpaper set` (or a successful
reconcile) and points at
`~/.local/state/dotfiles/current/colors.rasi`. If the bootstrap exposes the rofi
config before that consumer link exists, or if the runtime-seed step fails, rofi
exits with a theme parse error. The next successful wallpaper set creates the
link and “fixes” rofi — exactly the reported behavior.

## Repro (live host, non-destructive)

With the current palette present, rofi launches cleanly from any cwd:

```sh
cd /home/inumaki/Development
timeout 3 rofi -config ~/.config/rofi/launcher/config.rasi -show drun
# rc=124 (killed by timeout after opening), stderr empty
```

Remove the consumer symlink temporarily and launch again:

```sh
mv ~/.config/rofi/colors.rasi /tmp/rofi-colors.rasi.bak
timeout 6 rofi -config ~/.config/rofi/launcher/config.rasi -show drun
# rc=124, stderr includes:
# Failed to open theme: <i>/home/inumaki/Development/colors.rasi</i>
# Error: <b>No such file or directory</b>
# Validating the theme failed: the variable 'color01' ... failed to resolve.
mv /tmp/rofi-colors.rasi.bak ~/.config/rofi/colors.rasi
```

Restoring the link resolves all failures; the link target is
`/home/inumaki/.local/state/dotfiles/current/colors.rasi` and resolves to the
current palette entry.

## Evidence

- `~/.config/rofi/launcher/config.rasi:1` imports `../colors.rasi`.
- `~/.config/rofi/colors.rasi` is a symlink to
  `~/.local/state/dotfiles/current/colors.rasi`; its mtime was
  `2026-10-29 17:58:30 -05` after the latest wallpaper set, not at bootstrap end.
- `dotfiles-runtime wallpaper set` reports
  `consumer_symlinks` including `.../config/rofi/colors.rasi`.
- The bootstrap playbook order is `config_links` → `runtime-seed`; runtime-seed
  is the only producer of current/ and consumer symlinks
  (`dotfiles-provision/ansible/playbooks/runtime-seed.yaml`).
- runtime-seed tolerates `rc=1` (`failed_when: rc not in [0, 1]`) and only
  asserts that rc; it does not assert that the rofi consumer link exists.
- `verify` checks the rofi config dir but does not prove a usable
  `colors.rasi` at the moment a launcher can be opened.
- The observed bootstrap timeline on 2026-10-29: config-links/rofi tasks ran
  around 17:14–17:27; runtime-seed history has a successful CSG set at
  22:18:35Z (17:18:35 local); the rofi link was last recreated at 17:58:30.
  The original user failure was before that later set.

## Hypotheses / triage plan

1. **Bootstrap exposure window.** `config_links` links `~/.config/rofi` before
   `runtime-seed` has created the consumer palette links. A user who launches
   rofi during verify (or if runtime-seed fails/returns 1) sees the parse error.
2. **Silent seed failure.** runtime-seed accepts rc 1 and verify does not assert
   the rofi palette link; a failed derivation can therefore leave a green
   bootstrap with a broken launcher. Check the tpr/native helper gap in
   BUG-007: a tpr runtime-seed would have failed before the helper was
   installed.
3. **Hard import with no fallback.** The rofi config treats the runtime palette
   as mandatory; a missing link is fatal rather than falling back to a built-in
   theme. The config lives in `dotfiles-assets` (`configs/rofi`), so a fallback
   or a generated default is an alternative fix.

Triage should inspect the actual bootstrap output/log for runtime-seed and
whether the rofi link existed at the moment of the user launch; then choose the
minimum fix:

- Ensure `runtime-seed`/reconcile creates the consumer links before
  `config_links` exposes rofi, and fail the bootstrap if the link is absent; or
- make rofi's import resilient (fallback palette) and still assert the runtime
  link after seed.

## Done-when

- [ ] A fresh bootstrap followed immediately by a rofi launch has no theme
  parse error; rofi does not depend on the user switching wallpaper first.
- [ ] `runtime-seed` cannot silently pass with a missing rofi consumer link;
  either it creates the link or the bootstrap fails with the exact missing path.
- [ ] A regression check covers the missing-link state (rofi config parse or a
  structural assertion that `~/.config/rofi/colors.rasi` resolves).
- [ ] The fix is owned by `dotfiles-provision`; any rofi fallback change is
  cross-linked to `dotfiles-assets`, and any consumer-link change to
  `dotfiles-runtime`.

## Triage findings / decided fix (2026-10-29)

The failure is a real pre-seed exposure window plus a missing gate:

- `config_links` includes `rofi` and runs **before** `runtime-seed`; rofi’s
  `launcher/config.rasi:1` hard-imports `colors.rasi`, which runtime-seed owns.
- `verify_consumer_symlinks` currently asserts only the AGS link, not rofi (or
  gtk/btop), so a missing rofi palette link can pass verify.
- runtime-seed accepts rc 1 and only asserts rc; it does not prove fresh state
  or consumer links.

Proper fix (owner `dotfiles-provision`; runtime remains the config/link owner):

1. Split `config_links` into pre-seed settings links (`hypr`, `hyprpaper`,
   `nvim`, `starship`, `wlogout`, `zsh`, `kitty`, `color-scheme-generator`,
   `weg`, `itr`, `theme-producer`) and post-seed palette-consumer links
   (`gtk-3.0`, `gtk-4.0`, `rofi`, `btop`). Bootstrap order:
   config-links → runtime-seed → config-links-post-seed → display-manager →
   verify.
   Do not move the whole seed before config-links; the CLIs discover their
   settings through `~/.config/<tool>`.
2. runtime-seed: capture pre-state; after the set assert `current.json`
   advanced, the rofi link resolves, and all runtime consumer links exist.
   Accept rc 1 only when a fresh state/complete link set was produced; otherwise
   fail with the missing path.
3. verify: add rofi (and preferably gtk-3.0, gtk-4.0, btop) to
   `verify_consumer_symlinks`; assert the link is a symlink resolving under
   `dotfiles/current`.
4. A rofi fallback in assets is optional defense-in-depth only; it cannot
   replace the link/seed assertions.

## Cross-references

- `dotfiles-provision` BUG-007 — tpr native helper not provisioned; a probable
  cause of a failed tpr runtime-seed.
- `dotfiles-runtime` consumer-symlink seeding (`wallpaper set` / `reconcile`).
- `dotfiles-assets` rofi `launcher/config.rasi` hard import.

## Closeout evidence (2026-10-30)

- Bootstrap completed with the post-seed config-links phase; rofi
  `colors.rasi` exists and resolves to the current palette (created 07:56:42).
- `rofi -config ~/.config/rofi/launcher/config.rasi -show drun` opened with rc
  124 (timeout after open) and empty stderr, immediately after bootstrap.
- No manual ``ln -s``/wallpaper set was used to create the link.
