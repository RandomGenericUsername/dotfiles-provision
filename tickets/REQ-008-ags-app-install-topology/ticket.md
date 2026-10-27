---
id: REQ-008
title: "Generic per-app AGS install topology and one-owner cutover"
kind: requirement
status: done
lane: 3
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-008/
branch: ticket/REQ-008-ags-app-install-topology
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

- [x] The role consumes the app list + program tuple; the app-list schema validates.
      Evidence: `ags_apps_units` asserts the required fields, one owner, unique
      app/installDir/instance/config/spine/XDG surfaces, repo/tag rules and the
      single bar palette pointer; `program-tuple.yaml` is asserted as schemaVersion
      1 with exactly the three semver tags. Fixtures exercise legacy, mixed and
      all-standalone lists. `contracts` v0.3.0 owns the JSON Schemas.
- [x] Owner filters produce exactly one owner for every app in legacy, mixed and
      all-standalone fixtures. Evidence: `TestOwnerFilters` plus the old/new role
      execution tests.
- [x] Install path, shared platform shortcut, config/XDG/bin/launcher/autostart
      links and the bar palette pointer match the list. Evidence:
      `TestRoleExecution` asserts `<install>/apps/<installDir>/<tag>`, the one
      `apps/node_modules/ags-platform` shortcut, spine/XDG/bin/launcher links,
      `colors.css` -> the runtime state pointer and the assets-owned autostart
      identity (exactly once, under `ags-run-locked`).
- [x] Cutover quiesces, repoints, starts and verifies identity + handler + all
      ownership surfaces; rollback works; no hot link swap under a running app.
      Evidence: owner-flip, failure-rollback and tag-bump execution tests; quiesce
      runs before every link write and holds the shared launch lock.
- [x] Installed tags are verified immutable; `colors.css`/`icons.json` ownership
      is single-producer; the tag-bump state test passes. Evidence:
      `test_all_standalone_installs_full_topology_and_tags_stay_immutable`,
      `test_tag_bump_repoints_links_and_preserves_external_state`, and the
      installer/verify `_verify_unit.yml` checks (platform checksum equality).
- [x] The shared launch lock is used by every `ags run` path. Evidence: the
      `cli_tools/files/ags-run-locked` wrapper; all five provisioned launchers,
      gui_tools start-if-down paths, the generic launcher template and the
      installer start/rollback paths use it; verify and the installer enforce one
      locked autostart entry per standalone app. The pinned runtime `v0.2.3`
      uses the same `$XDG_RUNTIME_DIR/ags-launch.lock` (runtime BUG-006).
- [x] The verify mirror and deploy-coverage assertions match the new topology.
      Evidence: `_verify_standalone.yml`, owner-partition assertions, the
      per-owner generated-icon skeleton filter and the legacy-section gates. The
      composition `deploy-coverage` app-list gate already validates the same
      legacy/mixed/all-standalone fixtures and is unchanged; no composition pin
      moved.
- [ ] The old monorepo role/pin and old launcher/config entries are removed at
      program completion. Deferred by design: no app has cut over, so
      `ags_apps` remains the owner of all seven legacy entries and keeps its
      `v0.4.3` pin (`ags-platform v0.2.0`). The verification gate proves zero
      duplicate surfaces for a mixed list.
- [x] `make gates` is green; fake-app fixtures are GUI-free. Evidence below.

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

## Closeout (2026-10-27)

Local-only release; nothing pushed or published.

| Item | Value |
| --- | --- |
| Implementation commit | `59c42a8` — `feat(REQ-008): generic per-app AGS install topology and one-owner cutover` |
| Main merge | `459e3b2` — merge `main` (v0.1.17) into the ticket branch |
| Release commit | `0fd9f2d` — `chore(release): generic AGS install topology; v0.1.18` |
| Merge/tag commit | `543ff58` — merge `ticket/REQ-008-ags-app-install-topology`; tagged |
| Annotated tag | local `v0.1.18`, tag object `5848f17`, peeled commit `543ff58` |
| Engine version | `0.1.18` in `pyproject.toml`, `src/provisioning/__init__.py`, `uv.lock`; CHANGELOG `[0.1.18]` |

### Gates

- `make gates` → exit 0. Fast suite: **1032 passed, 3 skipped, 54 deselected**
  (20m43s); hermetic: **999 passed, 36 skipped, 54 deselected** (16m21s);
  `ruff check`, `uv lock --check`, `docs-check` all pass.
- `make ci-gates-parity` → PASS; gate/job sets match.
- `make build` → sdist + wheel `0.1.18`; wheel-contents check PASS.
- `openspec validate repo-birth --strict` → valid (this ticket has no OpenSpec
  change; `links.openspec: none`).
- Fake-app execution tests run real `ansible-playbook`: legacy no-op, mixed
  owner filter, all-standalone topology/tag immutability, owner flip,
  tag-bump/state preservation and rollback. No network clone, no GUI, no AGS
  host dependency.

### Fixtures added

- `tests/fixtures/ags-apps/app-list/{legacy,mixed,all-standalone}.apps.yaml`
- `tests/fixtures/ags-apps/fake-app/` (manifest, `app.tsx`, handler,
  `icons.json`, bin tool)
- `tests/fixtures/composition/dotfiles/provisioning/{apps.yaml,program-tuple.yaml}`
  (composition data records; the `manifests` CLI check skips them deliberately)

### Deliberate limits / blockers for a future cutover

- **No cutover and no composition pin move.** All seven `dotfiles-v3` entries
  remain `owner: legacy`; `dotfiles-v3` `installer.pin` stays `v0.1.17` until
  its own pin task consumes engine `v0.1.18`.
- **Adoption tuple mismatch is guarded.** The composition tuple names
  `ags-platform v0.3.0`, while the engine still pins `v0.2.0` for the legacy
  unit. `ags_apps_units` refuses to link a missing tuple platform unit, so a
  standalone flip before the adoption re-pin fails loud rather than shipping a
  dangling resolver.
- **Autostart lock content is assets-owned.** `dotfiles-assets v0.6.1` still
  starts the legacy instances with raw `ags run`. The installer and verify now
  require each standalone entry to appear exactly once as
  `--expect-instance <identity>` through `ags-run-locked`, so the assets
  autostart update must land in the same epoch as the first real cutover
  (dotfiles-assets REQ-007 / later assets release). This role intentionally
  never writes assets-owned content.
