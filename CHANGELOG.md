# Changelog

Notable changes to the `dotfiles-provision` repo. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow the git tags
(`vMAJOR.MINOR.PATCH`, annotated, never moved).

## [Unreleased]

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
