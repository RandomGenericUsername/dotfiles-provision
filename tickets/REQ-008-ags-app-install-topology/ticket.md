---
id: REQ-008
title: "Generic per-app AGS install topology and one-owner cutover"
kind: requirement
status: proposed
lane: 3
links:
  openspec: none
  bmad: none
worktree: none
branch: none
---

# Generic per-app AGS install topology and one-owner cutover

## Requirement

Replace the `ags_apps` monorepo role's hardcoded app blocks with one generic,
data-driven install/cutover role driven by the `dotfiles-v3` app list and
`program-tuple.yaml`.

Deliver:

- install each app at `<install>/apps/<installDir>/<tag>/`, with one shared
  `<install>/apps/node_modules/ags-platform` shortcut; the legacy monorepo keeps
  its per-unit shortcut to the same program tuple until removal;
- consume the app list's `owner: legacy|standalone` filter: the old role deploys
  only `legacy`, the new role only `standalone`; no duplicate owner;
- create/verify the config, spine, XDG and optional bin links, launcher and
  autostart entries from the app-list fields; the bar keeps its palette pointer;
- quiesce the old instance (confirmed quit), install/repoint, start the new
  instance, verify identity/manifest/handler and every ownership surface;
- make installed tags immutable; verify `colors.css`'s stable pointer and the
  single-produced `icons.json`; never write into a tag;
- provide the shared `ags-run-locked` wrapper and use it for autostart, on-demand
  launchers, runtime restart and provisioning;
- add the verify-role mirror and a fake-app cutover fixture covering quiesce →
  owner flip → install/start → verify and rollback;
- remove the old `ags_apps` role/pin and the old `gui_tools`/`config_links`/
  `cli_tools` app entries when the last app moves.

## Acceptance

- [ ] The role consumes the app list + program tuple; the app-list schema validates.
- [ ] Owner filters produce exactly one owner for every app in legacy, mixed and
      all-standalone fixtures.
- [ ] Install path, shared platform shortcut, config/XDG/bin/launcher/autostart
      links and the bar palette pointer match the list.
- [ ] Cutover quiesces, repoints, starts and verifies identity + handler + all
      ownership surfaces; rollback works; no hot link swap under a running app.
- [ ] Installed tags are verified immutable; `colors.css`/`icons.json` ownership
      is single-producer; the tag-bump state test passes.
- [ ] The shared launch lock is used by every `ags run` path.
- [ ] The verify mirror and deploy-coverage assertions match the new topology.
- [ ] The old monorepo role/pin and old launcher/config entries are removed at
      program completion; no duplicate config/XDG/bin/launcher/autostart/process.
- [ ] `make gates` is green; fake-app fixtures are GUI-free.

## Dependencies

- `dotfiles-v3` app list, program tuple and OpenSpec change.
- `contracts` REQ-009 install-list/program-tuple schemas.
- `dotfiles-runtime` REQ-002 / BUG-006 for the manifest runtime and safe restart.
- `dotfiles-assets` REQ-007 for the clipboard launch/keybind rename and lock
  wrapper inputs.

## Evidence

- Current monorepo role: `ansible/roles/ags_apps/vars/main.yml`,
  `tasks/main.yml`; verify role mirror.
- `ags-apps/_bmad-output/initiative-ags-standalone-apps/architecture-standalone-app-contract/architecture-standalone-app-contract.md`
  (AD-31, AD-32, AD-37).
