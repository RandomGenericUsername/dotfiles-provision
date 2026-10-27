# Changelog

Notable changes to the `dotfiles-provision` repo. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow the git tags
(`vMAJOR.MINOR.PATCH`, annotated, never moved).

## [Unreleased]

## [0.1.17] - 2026-10-26

### Changed

- **`color-scheme-generator` pin `v0.2.1` (csg BUG-001):** container-mode
  `generate`/`show` now label their wrappers as csg-owned (`csg.managed`,
  `csg.session`, `csg.created_at`, `csg.timeout_seconds`, plus `csg.boot_id`
  when exposed) and run a best-effort sweep before image preflight. wrappers
  from a previous boot are removed immediately; same-boot wrappers only after
  their own timeout plus a 60 s grace. Young same-boot wrappers from a
  concurrent run, unlabelled/foreign containers, and wrappers with no parseable
  age are left untouched; list/inspect/remove failures are logged and never
  fail the requested palette run. The engine pins the tag in `cli_tools`, the
  assets csg-template mirror (`assets_csg_pinned_tag`), the settings rendered
  image tag (`settings_csg_image_tag`), `verify_csg_version`, and the fixture
  `cli-tools.yaml` + `assets.yaml` source. `verify_csg_contract_version` stays
  `0.2.0` (`csg --version` prints `0.2.1 contract 0.2.0`); the assets corpus
  pin stays `v0.6.1`.
- **`dotfiles-runtime` pin `v0.2.3` (runtime BUG-005):** an absent optional
  intent root is informational instead of degraded watch health. The optional
  `$XDG_CONFIG_HOME/dotfiles/desired.json` root reports `optional_absent` at
  INFO, only a required-root failure sets `failed_roots`/`degraded`,
  `watch-health.json` gains the additive `optional_absent` key under the
  unchanged `version: 1`, `inspect daemon`/`doctor` stay exit 0 while printing
  `OPTIONAL (absent, not watched)`, and `WatchCoordinator` retries once per
  burst when an optional root is absent. The engine's `cli_tools` mirror, the
  hand-maintained verify mirror (`verify_runtime_version` /
  `verify_runtime_tool_version`) and the fixture `cli-tools.yaml` move from
  `v0.2.2` to `v0.2.3`.

### Notes

- No assets-corpus, ags-apps, weg, itr or ags-platform pin moves; the assets
  tag stays `v0.6.1` and every `verify_*_contract_version` stays `0.2.0`.
- This release adds no engine-side runtime install pin. The host deploy and
  live verification are user-run after the `dotfiles-v3` `PIN-0116`
  re-provision.

## [0.1.16] - 2026-10-26

### Changed

- **`dotfiles-assets` pin `v0.6.1` (assets BUG-001):** the wlogout Logout tile
  now runs `uwsm stop` instead of `loginctl terminate-user $USER`, so logout
  stops the compositor unit and lets the SDDM helper exit normally instead of
  tearing down every user session (the `sddm-helper` SIGHUP crash behind the
  black VT; provision BUG-005). Every `*_assets_pinned_tag` mirror moves from
  `v0.6.0` to `v0.6.1` (assets, btop_config, compositor_configs,
  config_copies, display_manager, kitty_config, verify, wlogout_config,
  zsh_config), and the fixture composition manifest carries the same tag in
  `assets.tag` and its three checkout sources. The corpus is otherwise
  unchanged.
- **`dotfiles-runtime` pin `v0.2.2` (runtime BUG-003; BUG-004 retained):** the
  icon-contrast prefs reader now accepts its own canonical document at any
  entry count (four or more prefs round-trip instead of falling back to
  defaults), and BUG-004's btop-theme-studio skip stays so a wallpaper change
  does not discard unsaved studio edits. The engine's `cli_tools` mirror, the
  hand-maintained verify mirror (`verify_runtime_version` /
  `verify_runtime_tool_version`) and the fixture `cli-tools.yaml` move from
  `v0.2.0` to `v0.2.2`, locked by `TestVerifyRuntimePinMirror`.

### Fixed

- **Logout returns to the greeter instead of a black VT (provision BUG-005):**
  consuming assets `v0.6.1` ships the one-line `uwsm stop` logout action; the
  host acceptance (logout → greeter, then five logins) runs after the
  `dotfiles-v3` `PIN-0115` re-provision. This release adds no engine-side
  runtime install pin; the composition install pin remains in `dotfiles-v3`.

## [0.1.15] - 2026-10-26

### Changed

- **`dotfiles-runtime` pin `v0.2.0` (runtime BUG-001):** the runtime palette is
  mandatory — applying a scheme either generates a palette or fails with a
  traceable error and keeps the last-good state; `palette: null` is gone. The
  engine's `cli_tools` mirror and its hand-maintained verify mirror both move
  from `v0.1.0` to `v0.2.0` (`verify_runtime_version` /
  `verify_runtime_tool_version`), locked by `TestVerifyRuntimePinMirror`. The
  composition manifest (`dotfiles-v3/dotfiles/provisioning/cli-tools.yaml`) and
  `installer.pin` move in the same deploy in `PIN-0114`. No ags-apps or assets
  pin moves.

## [0.1.14] - 2026-10-26

### Changed

- **`ags-apps` pin `v0.4.3` (ags-apps BUG-002):** the wallpaper selector now
  collapses its drawer immediately on Apply instead of staying open over the
  wallpaper change; the apply completes and a palette error surfaces through
  the notification. The engine installs the monorepo unit at v0.4.3
  (`ags_apps_version`) and the verify mirror (`verify_ags_apps_version`)
  follows, locked by `TestVerifyAgsAppsPinMirror`. No runtime or assets pin
  moves.

## [0.1.13] - 2026-10-26

### Fixed

- **SDDM's Wayland greeter had no compositor (BUG-004):** the rendered
  `/etc/sddm.conf.d/10-dotfiles.conf` set `DisplayServer=wayland` while none of
  `weston`/`kwin_wayland`/`cage`/`sway`/`wayfire`/`labwc` was installed. The
  greeter display server could not start, so SDDM silently fell back to
  `DisplayServer=x11-user` on every login, the session got a new VT, and it was
  torn down ~90 s later (`Session started false`; 4 fallbacks on the
  2026-10-26 boot). The role now installs `weston`, renders
  `[Wayland] CompositorCommand=weston --shell=kiosk` from the assets v0.6.0
  template (`req-006`), and fails closed with a `command -v weston` preflight
  instead of accepting the fallback. The Pixie theme is pinned to the tested
  commit `1e1a8637` (was the moving `main`) and the `interval: 5000`
  login-timeout patch now fails if the pattern is absent or duplicated. `verify`
  statically asserts weston, the Wayland config lines, the Pixie HEAD and the
  applied patch (it never restarts SDDM). Every `*_assets_pinned_tag` mirror
  moves to v0.6.0. The greeter change takes effect after the next host
  provision + reboot.

## [0.1.12] - 2026-10-25

### Fixed

- **`ags-apps` pin `v0.4.2` (ags-apps BUG-001):** the wallpaper-selector
  rendered every PNG card in black & white — gdk-pixbuf's JPEG writer
  mishandles 4-channel (RGBA) pixbuf buffers, so all disk thumbnails derived
  from `.png` sources stored fully desaturated jpegs that kept re-hitting
  forever (the cache key counts path+mtime+size, which never move). ags-apps
  `49adc30`/`v0.4.2` flattens RGBA onto an opaque 3-channel pixbuf over black
  before the save and bumps the thumb-cache entry format to v2, so the
  poisoned entries fall out on the first open of the fixed build. The verify
  mirror (`verify_ags_apps_version`) moves to v0.4.2 with the pin.

## [0.1.11] - 2026-10-24

### Fixed

- **`power-options` kept the old profile in memory (v0.1.10 regression):** the
  daemon reads profile TOMLs at startup; `refresh-full` alone left Powersave
  blocking Bluetooth after the file rewrite. The role now restarts
  `power-options.service` after a change, then refreshes. The marker content
  carries `policy_version = 2`, so upgrading a host whose TOMLs are already
  false still restarts the daemon once. Verified live after restart: Powersave
  keeps `rfkill` unblocked.

## [0.1.10] - 2026-10-24

### Added

- **`power_options` role (REQ-003):** `power-options-daemon` ships
  `block_bt = true` in Powersave/Powersave++/Balanced, so switching profiles
  soft-blocked Bluetooth. The role rewrites `block_bt` to false in those three
  profiles, refreshes the active profile only when a file changed, and writes
  `/etc/power-options/.dotfiles-bt-ok` as the applied marker. It is a no-op when
  `/etc/power-options/profiles` is absent (non-Arch). `verify` reads the three
  profiles and fails if any still blocks Bluetooth; it skips when the marker is
  absent.

## [0.1.9] - 2026-10-24

### Fixed

- **Installed wheel dropped `inventory/group_vars` (BUG-002):** the source kept
  group_vars at `ansible/group_vars` with an `inventory/group_vars` symlink; the
  sdist/wheel build silently dropped the symlink, so the installed engine's
  `verify` lost `container_runtime_engine` and `shell`. The canonical files now
  live in the real `ansible/inventory/group_vars/` directory, and `make build`
  runs `scripts/check-wheel-contents.py`, which fails if the wheel lacks the
  inventory or any group_vars file.

## [0.1.8] - 2026-10-23

### Fixed

- **`runtime-seed` ran a deleted source tree (BUG-001):** the playbook still invoked
  `uv run --directory {{ composition_root }}/src/runtime`, which the composition deleted in
  REQ-002, so a fresh bootstrap would fail after `cli_tools`. It now runs the installed pinned
  `{{ runtime_seed_bin_dir }}/dotfiles-runtime` (the same uv-bin-dir resolution as
  `cli_tools_bin_dir` / `runtime_daemon_bin_dir`). No `composition_root` requirement remains in
  the seed play. A unit test locks the argv and the absence of the source path.

## [0.1.7] - 2026-10-23

### Changed

- **`dotfiles-runtime` is a pinned CLI entry (REQ-002):** the runtime was extracted to
  `RandomGenericUsername/dotfiles-runtime` and tagged `v0.1.0`. The `cli_tools` role mirror now
  carries `{repo, tag}` for it, so all four CLI entries are pinned and the source-path loop
  selects nothing. `verify` adds `dotfiles-runtime` to `verify_cli_tools` and asserts the
  tag-bearing checkout, the `pinned` record and `dotfiles-runtime version` = `0.1.0`. The
  source-path install/upgrade branch and its tasks remain as the extension point for a future
  in-repo tool. The composition's `installer.pin` bump and `src/runtime/` deletion land in
  `dotfiles-v3`.

## [0.1.6] - 2026-10-23

### Fixed

- **`verify` ags-apps pin mirror (v0.1.5 regression):** `ags_apps_version` advanced to `v0.4.1`
  but `verify_ags_apps_version` stayed at `v0.4.0`, so the first post-apply verify failed on the
  live-bar symlink assertion. The mirror is now `v0.4.1`; a parity test
  (`TestVerifyAgsAppsPinMirror`) locks both the unit and platform versions to the `ags_apps` role.

## [0.1.5] - 2026-10-23

### Fixed

- **Bootstrap failure in the R-14 rendered-unit assert (v0.1.4 regression):** the `that:` string
  contained literal `{%`/`%}`, which Ansible parsed as a Jinja block before evaluating and failed
  with `tag name expected` / `CapturedExceptionMarker`. The assert now uses the `[{]%` and `%[}]`
  character classes, which match the same delimiters without spelling them out. Verified:
  `ansible-playbook ansible/playbooks/runtime-daemon.yaml` → `failed=0`; unit tests `32 passed`.

## [0.1.4] - 2026-10-23

### Fixed

- **btop integration test seam (R-07):** the direct `btop-config.yaml` run now passes
  `composition_root`, which the legacy active-theme migration stat reads. Test-only fix; the
  v0.1.3 role behavior is unchanged. `pytest tests/integration/test_btop_theme_deployment_e2e.py
  -q` → `2 passed`.

## [0.1.3] - 2026-10-23

### Changed

- **btop active-theme is host state in the install spine (R-07):** `btop_config` reads
  `<install>/config/btop/active-theme` instead of `dotfiles/config/btop/active-theme`. A
  pre-R-07 composition file is used once to seed the spine, so an existing selection survives the
  migration. The composition repo no longer authors a `dotfiles/config/` tree.
- **`ags-apps` pin `v0.4.1`:** the btop studio now writes the active theme through
  `activeThemePath()` into the install spine (`<install>/config/btop/active-theme`), matching the
  role. `make btop-theme-studio-tests` is green in the studio repo.

## [0.1.2] - 2026-10-22

### Added

- **Stale uv-tool metadata assert (R-14):** after the force re-installs, `cli_tools` scans every
  `direct_url.json` under the uv tool root and fails naming any `file://` checkout that no longer
  exists. The force install is the repair; the assert proves a package-tree move cannot leave a
  console script that starts and then dies with `ModuleNotFoundError`.
- **Rendered daemon unit assert (R-14):** `runtime_daemon` slurps the deployed unit and fails if
  `ExecStart` carries an unresolved `{%`/`%}` or a swallowed `#` continuation (the
  `start-limit-hit` trap). Check-mode safe; the existing `reset-failed` remains before enable/start.

## [0.1.1] - 2026-10-22

Engine hardening from the assets-split residual ledger. No corpus or runtime behavior change.

### Added

- **Self-contained wheel (R-15):** `ansible/` ships as package data under
  `provisioning/_ansible` (hatch wheel `force-include`); `cli/main.py` resolves it through
  `importlib.resources` and keeps the repo-root `ansible/` fallback for editable checkouts.
  `uv tool install git+…@v0.1.1` now resolves every playbook/inventory/config path without a
  checkout. Child `ansible`/`ansible-playbook` lookups also prepend the interpreter's bin dir
  (uv exposes only the project entry point on the tool bin dir), so the tool runs playbooks with
  no ansible-core scripts installed globally.
- **Engine-pin assertion in verify (R-17):** `verify --expected-engine-tag vX.Y.Z` forwards the
  role's `expected_engine_tag` extra-var, runs `dotfiles-provision --output-format plain version`
  and fails when it differs from the composition's `installer.pin`; both tasks are `engine`-tagged
  and check-mode safe. Empty by default for hand-run development verifies.
- **`make assets-parity` + CI job (R-01):** clone `dotfiles-assets` at the pinned tag, export
  `DOTFILES_ASSETS_REPO` / `DOTFILES_ASSETS_TEMPLATES_DIR`, run the AD-8.4 parity module, and fail
  on any skip or clone failure (fail-closed). Declared in `CI_ONLY_EXEMPT`, so `gates-ci` keeps its
  five members.
- **`reset-failed` before daemon enable/start (R-14):** the runtime daemon unit is cleared of a
  previous `start-limit-hit` before `systemd` enable/start, manager-probe gated and check-safe.

### Fixed

- **`TestVerifyRuntime` fixture (R-02):** the synthetic machine already carries the pinned
  `cli-tools/{csg,weg,itr}/<tag>/` checkouts, `pinned` records and contract handshake stubs added
  in `e11daa4`; this release also repairs the WEG negative-lock stub so it fails on `weg info`
  while still reporting the pinned `--version`. The full class remains a developer
  `make test-integration` run and R-02 stays open: it executes the whole verify role per test and
  exceeds the residual sweep's five-minute budget, so no green execution is claimed here.

## [0.1.0] - 2026-10-22

First release. The engine content is the in-tree provisioning project imported from
`dotfiles-v3` (`ansible/`, `src/provisioning/`, `tests/`), history preserved.

### Added

- The provisioning engine at the repo root: 21 Ansible roles, 23 playbooks, the hexagonal Python
  orchestrator (`plan` / `apply` / `verify` / `bootstrap`), and the seam contract that wires them.
- The **composition seam** (AD-17): `--manifests-dir`, `--composition-root` and `--inventory`
  resolved once by the CLI and passed to Ansible as `manifests_dir` / `composition_root`
  extra-vars. The read-only `manifests` command resolves every manifest through the real reader.
- `tests/support.py` and `tests/fixtures/composition/`: the moved unit tests resolve the
  composition from a byte-copied fixture (or `$DOTFILES_COMPOSITION_ROOT`), never from a dotfiles
  checkout above the engine.
- `tests/unit/test_composition_seam.py`: the executable seam guard (external manifests dir, loud
  failures, and a static scan proving no YAML value or Jinja template derives from
  `playbook_dir`).
- Repo harness copied byte-for-byte from `mu`: `scripts/worktree-guard.sh`, `skills-lock.json`,
  `_bmad/`, `.agents/skills/`, `.opencode/`, `tickets/_template/`, `tickets/_fixtures/`,
  `tickets/LIFECYCLE.md`.
- `Makefile` fresh-clone verbs (`sync`, `test`, `test-integration`, `lint`, `format`, `hermetic`,
  `lock-check`, `docs-check`, `gates`, `gates-ci`, `build`, `install`, `clean`,
  `ci-gates-parity`), `.github/workflows/gates.yml`, and `scripts/ci-gates-parity.py`.
- MIT `LICENSE`, `README.md`, `AGENTS.md`, `CLAUDE.md` symlink, ticket `REQ-001-repo-birth`, and
  the OpenSpec change `repo-birth` plus the `repo-harness` spec.

### Changed

- Every `{{ playbook_dir }}/../../../..` repo-root derivation is gone: `btop_config` and
  `cli_tools` read the seam, `runtime-seed` runs the composition's runtime through
  `composition_root`, and the pinned-asset roles (`assets`, `compositor_configs`,
  `config_copies`, `gui_tools`, `zsh_config`, `wlogout_config`) read their checkouts instead.
- `pyproject.toml`: release metadata (`readme`, license classifier) and an sdist `only-include`
  that keeps the harness trees out while shipping `ansible/` for source installs.
- Tests that asserted the composition's provisioning-shape gate or `bootstrap.sh` were retired
  from this repo (they belong to `dotfiles-v3`); the manifest-parity tests now read the fixture.
