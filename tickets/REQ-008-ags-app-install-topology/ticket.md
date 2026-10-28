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
- [x] The old monorepo role/pin and old launcher/config entries are removed at
      program completion. Evidence (v0.1.21): `ansible/roles/ags_apps/` and
      `ansible/playbooks/ags-apps.yaml` are deleted; `ags_apps_units` rejects a
      `legacy` entry and owns all seven standalone apps. `cli_tools` no longer
      renders AGS launchers, `gui_tools` no longer tracks AGS instances,
      `config_links` no longer exposes AGS basenames, and `compositor_configs`
      no longer generates/validates AGS icons. The all-standalone fixture and
      execution tests prove one owner per surface and no legacy role.
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
  its own pin task consumes engine `v0.1.19`.
- **Adoption tuple is active (resolved in v0.1.19).** The legacy unit now
  installs `ags-apps v0.5.0`; `ags_platform` installs `v0.3.0`; and the shared
  shortcut plus the legacy per-unit shortcut both resolve that same tuple.
  Verify mirrors assert the same three values. `ags_apps_units` remains a no-op
  while every entry is legacy.
- **Autostart lock content is assets-owned.** `dotfiles-assets v0.6.1` still
  starts the legacy instances with raw `ags run`. The installer and verify now
  require each standalone entry to appear exactly once as
  `--expect-instance <identity>` through `ags-run-locked`, so the assets
  autostart update must land in the same epoch as the first real cutover
  (dotfiles-assets REQ-007 / later assets release). This role intentionally
  never writes assets-owned content.

## Follow-up closeout — adoption tuple (v0.1.19)

Local-only release; nothing pushed or published.

| Item | Value |
| --- | --- |
| Pin/test commit | `4a9ec99` — `feat(pins): activate the ags-apps v0.5.0 + ags-platform v0.3.0 adoption tuple` |
| Release commit | `6b8e605` — `chore(release): activate the adoption tuple; v0.1.19` |
| Merge/tag commit | `0805db0` — merge `ticket/REQ-008-ags-app-install-topology`; tagged |
| Annotated tag | local `v0.1.19`, tag object `2d81165`, peeled commit `0805db0` |
| Engine version | `0.1.19` in `pyproject.toml`, `src/provisioning/__init__.py`, `uv.lock`; CHANGELOG `[0.1.19]` |
| Pins activated | `ags-apps v0.5.0`; `ags-platform`, `ags_apps_platform` and both verify platform mirrors `v0.3.0` |

### Gates

- Role/verify/bootstrap targeted suite → **240 passed** (includes real
  `ansible-playbook` role executions and the verify green/negative paths).
- `make gates` → exit 0. Fast suite: **1033 passed, 3 skipped, 54 deselected**
  (19m49s); hermetic: **1000 passed, 36 skipped, 54 deselected** (16m08s);
  `ruff check`, `uv lock --check`, `docs-check` all pass.
- `make ci-gates-parity` → PASS.
- `make build` → sdist + wheel `0.1.19`; wheel-contents check PASS.
- `ansible-playbook --syntax-check` for `ags-apps.yaml` and
  `ags-platform.yaml` → pass.

### Scope / safety

- `ags-apps v0.5.0` and `ags-platform v0.3.0` are local-only dependency tags.
  The role tests pre-seed the unit trees; the presence-guarded clone paths mean
  no gate fetches either tag.
- No app cutover, no `dotfiles-v3` change, no `hypr-pano` rename and no runtime
  pin move; `dotfiles-runtime` stays `v0.2.3`.

## Follow-up closeout — clipboard cutover preparation (v0.1.20)

Local-only release; nothing pushed or published. This prepares the engine for
the first real per-app cutover without flipping the composition or provisioning
the host.

| Item | Value |
| --- | --- |
| Implementation commit | `ea44d91` — `feat(REQ-008): prepare the clipboard launcher and config cutover` |
| Test-fixture fix | `9ba06d7` — `test(REQ-008): seed the clipboard spine dir for the verify fixture` |
| Release commit | `c8f55c8` — `chore(release): prepare the clipboard cutover; v0.1.20` |
| Merge/tag commit | `b31f2f3` — merge `ticket/REQ-008-ags-app-install-topology`; tagged |
| Annotated tag | local `v0.1.20`, tag object `323a077`, peeled commit `b31f2f3` |
| Engine version | `0.1.20` in `pyproject.toml`, `src/provisioning/__init__.py`, `uv.lock`; CHANGELOG `[0.1.20]` |

### Cutover support landed

- `cli_tools` renders **`clipboard-ui`** (was `hypr-pano-ui`): instance
  `clipboard`, window `clipboard-window`, dir `~/.config/ags-clipboard`, log
  `~/.local/state/ags/clipboard.log`, cold start
  `ags-run-locked --expect-instance clipboard`, warm `ags request toggle`.
  The install task keys on `'clipboard' in cli_tools_legacy_app_names`, so the
  legacy launcher disappears as soon as the app list says standalone.
- `gui_tools` carries the on-demand `clipboard` instance (was `hypr-pano`).
- `config_links` exposes `ags-clipboard` (was `ags-hypr-pano`); the legacy-owner
  filter drops that basename when the app list says standalone.
- `verify` asserts `clipboard-ui` and the `ags-clipboard` managed link.
- New fixture `tests/fixtures/ags-apps/app-list/clipboard.apps.yaml` models the
  v3 follow-up entry and drives a real `ansible-playbook` cutover test: install
  `<install>/apps/clipboard/<tag>`, spine link `<install>/config/ags-clipboard`,
  XDG link `~/.config/ags-clipboard`, locked `clipboard-ui` launcher, and the
  assets-owned `clipboard` autostart identity exactly once. The test also
  asserts the legacy `ags-hypr-pano`/`hypr-pano-ui` surfaces are not created.
- The old `ags_apps` monorepo role still filters `owner: legacy`; its legacy
  live-pano link is gated on the old `hypr-pano` id, so a `clipboard`
  standalone entry is never touched by the old role.

### Gates

- `make gates` → exit 0. Fast suite: **1037 passed, 3 skipped, 54 deselected**
  (20m33s); hermetic: **1004 passed, 36 skipped, 54 deselected** (16m47s);
  `ruff check`, `uv lock --check`, `docs-check` all pass.
- `make ci-gates-parity` → PASS.
- Targeted integration proof
  (`test_verify_passes_on_a_provisioned_machine`) → **1 passed** with the
  clipboard-managed link seeded.
- `make build` → sdist + wheel `0.1.20`; wheel-contents check PASS.

### Exact v3 follow-up (not edited here)

1. **Rename and flip the app-list entry** in
   `dotfiles-v3/dotfiles/provisioning/apps.yaml`:
   `app: hypr-pano` → `clipboard`, `installDir: hypr-pano` → `clipboard`,
   `owner: legacy` → `standalone` with the released `ags-clipboard` repo/tag,
   `instance: clipboard`,
   `configDir/configLink/spineLink/xdgLink: ags-clipboard`,
   `launcher: clipboard-ui`, `autostart: clipboard`, `launch: on-demand`.
2. **Bump the assets pin** to `v0.6.2` (the release whose autostart and keybind
   already call `clipboard-ui` / `~/.config/ags-clipboard`).
3. **Bump the engine pin** (`installer.pin` / expected engine tag) to
   `v0.1.20`.
4. **Apply the composition** and verify the four surfaces: `ags list` shows
   `ags/capture/notifications/clipboard`, `SUPER+V` opens the overlay,
   `~/.local/state/ags/clipboard.log` is written, and
   `~/.config/ags-clipboard` resolves through
   `<install>/config/ags-clipboard` to `<install>/apps/clipboard/<tag>`.

## Follow-up closeout — final all-standalone activation (v0.1.21)

Local-only release; nothing pushed, published or provisioned. This activates
the final topology in the engine and retires the legacy monorepo owner.

| Item | Value |
| --- | --- |
| Implementation/release commit | `4f2552f` — `feat(REQ-008): activate the final all-standalone AGS topology; v0.1.21` |
| Check-mode fix | `31cd0c9` — `fix(REQ-008): keep fresh-host --check dry for standalone verification` |
| Merge/tag commit | `1a9b769` — merge `ticket/REQ-008-ags-app-install-topology`; local annotated `v0.1.21` on `d652fc9` (tag object `5e6982414565dbd0970d77b6dc2d5669706e9cb7`, peeled `d652fc9`) |
| Engine version | `0.1.21` in `pyproject.toml`, `src/provisioning/__init__.py`, `uv.lock`; CHANGELOG `[0.1.21]` |

### Activation landed

- `ags_apps_units` is the only AGS installer/owner. Every app-list entry must be
  `owner: standalone`; the role installs every app at
  `<install>/apps/<installDir>/<tag>`, creates the ONE
  `<install>/apps/node_modules/ags-platform` shortcut, and owns each app's
  config/spine/XDG/bin/launcher surfaces, always-on starts and rollback.
- The old `ags_apps` role/pin, its playbook and tests are deleted. `cli_tools`,
  `gui_tools`, `config_links` and `compositor_configs` no longer own any AGS app
  surface.
- Launcher behavior is preserved through the app-list `launcher` field and the
  generic template: request-toggle (clipboard), window-toggle fallbacks
  (capture/selector/icme/studio), cold start under `ags-run-locked`, reveal via
  `request show`. The bar and notifications remain installer-started.
- `gui-tools` now runs before `ags-apps-units` so dunst is masked before the
  notifications overlay starts.
- The assets pin moves to `v0.6.2` (launch-lock autostart + clipboard rename);
  the verbatim v0.6.2 autostart fixture drives the one-locked-entry assertion.
- The bar tag (v0.1.1 after its state migration) carries `colors.css` as the
  stable pointer to `$XDG_STATE_HOME/dotfiles/current/colors.gtk.css` and the
  platform-produced `icons.json`; the role verifies both and writes neither.

### Gates

- `make gates` → exit 0. Fast suite: **897 passed, 31 skipped, 54 deselected**
  (21m58s); hermetic: **894 passed, 34 skipped, 54 deselected** (20m33s);
  `ruff check`, `uv lock --check`, `docs-check` all pass.
- `make ci-gates-parity` → PASS.
- `make build` → sdist + wheel `0.1.21`; wheel-contents check PASS.
- Targeted execution proof: seven-app all-standalone install, second-run tag
  immutability, rollback/restart, tag bump/state preservation, and launcher
  toggle/request behavior and fresh-host `--check` dryness all pass (GUI-free, local fake repos, no network).

### Exact v3 final-cutover follow-up (not edited here)

All seven entries MUST flip in ONE `dotfiles-v3/dotfiles/provisioning/apps.yaml`
commit — this engine fails loud on any `owner: legacy` entry because the legacy
installer no longer exists.

1. **Flip all seven entries** to `owner: standalone` with released
   `repo`/`tag`:
   - `bar` (`installDir: bar`, `instance: ags`, `configDir/configLink/spineLink/xdgLink: ags`, `launcher: none`, `autostart: ags`, `launch: always`, `barPalettePointer: true`) at `ags-bar` **v0.1.1** (the state-migration tag that carries `colors.css`).
   - `notifications` (`ags-notifications`, instance `notifications`, `ags-notifications`, `autostart: notifications`, `launch: always`) at `ags-notifications` v0.1.0.
   - `capture` (`installDir: capture`, `ags-capture-tool` repo, instance `capture`, `ags-capture`, `binLink: capture-tool`, `launcher: capture-ui`, `autostart: capture`, `launch: on-demand`) at `ags-capture-tool` v0.1.0.
   - `clipboard` (`installDir: clipboard`, `ags-clipboard`, instance `clipboard`, `ags-clipboard`, `launcher: clipboard-ui`, `autostart: clipboard`, `launch: on-demand`) at `ags-clipboard` v0.1.0. Replace the old `hypr-pano` entry; the legacy name must not remain.
   - `wallpaper-selector` (`ags-wallpaper-selector`, `launcher: wallpaper-selector-ui`, `launch: on-demand`) at v0.1.0.
   - `icme` (`ags-icme`, instance `icon-color-mapping-editor`, `ags-icme`, `launcher: icon-color-mapping-editor`, `launch: on-demand`) at v0.1.0.
   - `btop-theme-studio` (`ags-btop-theme-studio`, instance `btop-theme-studio`, `ags-btop-studio`, `launcher: btop-theme-studio`, `launch: on-demand`) at v0.1.0.
2. **Bump `program-tuple.yaml`**: `dotfiles-assets: v0.6.2`, `ags-platform:
   v0.3.0`, `contracts: v0.3.0`, `schemaVersion: 1`.
3. **Bump `dotfiles/provisioning/assets.yaml`**: `tag: v0.6.2` and its three
   `source:` checkout paths.
4. **Bump the engine pin** (`installer.pin` / expected engine tag) to
   `v0.1.21`.
5. Apply the composition. Expected host proof: `ags list` shows
   `ags`/`notifications` always-on; `capture`/`clipboard` autostart after their
   staggered delays; `~/.config/<xdgLink>` resolves through
   `<install>/config/<spineLink>` into `<install>/apps/<installDir>/<tag>`;
   `~/.local/bin/{capture-ui,clipboard-ui,wallpaper-selector-ui,icon-color-mapping-editor,btop-theme-studio}`
   are present and toggle warm instances; `~/.local/state/ags/*.log` is written;
   the bar's `colors.css` resolves to
   `$XDG_STATE_HOME/dotfiles/current/colors.gtk.css`; and no
   `<install>/ags-apps/` tree or `ags-hypr-pano`/`hypr-pano-ui` surface exists.

### Deliberate limits / blockers

- The bar `v0.1.1` state-migration tag does not exist in the local `ags-bar`
  checkout yet (only `v0.1.0`). The v3 cutover cannot use this engine until
  that app tag is created; this engine verifies the tag-carried pointer but
  never authors it.
- All seven app repos are local-only `v0.1.0` tags; no push/publish occurs in
  this ticket.
- No host provision was run in this ticket.

> Tag note: `v0.1.21` was first created on the mergeless ticket tip before the
> fresh-host `--check` fix and then re-pointed to `d652fc9` (the final v0.1.21
> tree with that fix) before any push/publish. It is local-only. A concurrent
> REQ-010 ticket took main to v0.1.22; this tag remains the REQ-008 release.

## Follow-up closeout — consume dotfiles-runtime v0.3.0 (v0.1.23)

Local-only release; nothing pushed, published or provisioned. Pin-only engine
release on top of the final all-standalone topology.

| Item | Value |
| --- | --- |
| Pin/release commit | `2c2cf46` — `chore(release): consume dotfiles-runtime v0.3.0; v0.1.23` |
| Merge/tag commit | `706bfce` — merge `ticket/REQ-008-ags-app-install-topology`; local annotated `v0.1.23` (tag object `78373608071dfcab42a38e5a28981bf2f7880ef9`, peeled `706bfce`) |
| Engine version | `0.1.23` in `pyproject.toml`, `src/provisioning/__init__.py`, `uv.lock`; CHANGELOG `[0.1.23]` |
| Runtime tag | local `dotfiles-runtime v0.3.0` (tag object `7c0f43b872a615ad47ff1a536dd89fa6569064ec`, peeled `dd615432bb5598432afeb8dd4425fdec8ecdd06b`) |

### Pin table (all legs agree)

| Consumer | Value |
| --- | --- |
| `roles/cli_tools/vars/main.yml` → `dotfiles-runtime` | `v0.3.0` |
| `roles/verify/vars/main.yml` → `verify_runtime_version` | `v0.3.0` |
| `roles/verify/vars/main.yml` → `verify_runtime_tool_version` | `0.3.0` |
| `tests/fixtures/composition/dotfiles/provisioning/cli-tools.yaml` | `v0.3.0` |
| Runtime/verify execution fixture | derives from the verify vars (prints `0.3.0`) |

Unchanged pins: `ags-platform v0.3.0`, `contracts v0.3.0`,
`dotfiles-assets v0.6.2`, `csg v0.2.1`, `weg v0.2.0`, `itr v0.2.0`,
`tpr v0.1.0`.

### Why v0.3.0

Runtime v0.3.0 brings the manifest-driven AGS palette refresh, the
applied-appearance ledger, the BUG-006 shared serialized restart/confirm lane
and the clipboard namespace migration — the runtime half of the standalone
app topology. The engine's existing shared `ags-launch.lock` and
`$XDG_STATE_HOME/dotfiles/` contracts match it; no provision-role code changes.

### Gates

- `make gates` → exit 0. Fast suite: **910 passed, 31 skipped, 54 deselected**
  (22m58s); hermetic: **907 passed, 34 skipped, 54 deselected** (20m44s);
  `ruff check`, `uv lock --check`, `docs-check` all pass.
- `make ci-gates-parity` → PASS.
- `make build` → sdist + wheel `0.1.23`; wheel-contents check PASS.
- Runtime-pin/verify tests: `TestVerifyRuntimePinMirror`,
  `test_runtime_mirrors_are_v0_3_0`, and the cli_tools pinned-entry tests pass.

### Exact v3 follow-up (not edited here)

1. In `dotfiles-v3/dotfiles/provisioning/cli-tools.yaml`, set the
   `dotfiles-runtime` entry to `repo:
   https://github.com/RandomGenericUsername/dotfiles-runtime` and
   `tag: v0.3.0`.
2. Bump `installer.pin` / the expected engine tag to `v0.1.23`.
3. Keep `dotfiles-assets v0.6.2`, `ags-platform v0.3.0` and
   `contracts v0.3.0` unchanged; no app-list change is needed (v0.1.22 already
   carries the all-standalone topology).
4. Apply and verify: `dotfiles-runtime version` reports `0.3.0`, the
   `~/.local/share/dotfiles/cli-tools/dotfiles-runtime/v0.3.0/` checkout and
   `pinned` agree, and the clipboard namespace migration completes under the
   runtime's own state migration (provisioning does not author runtime state).

### Deliberate limits

- `dotfiles-runtime v0.3.0` is a local-only tag; no push/publish.
- No host provision in this release.
