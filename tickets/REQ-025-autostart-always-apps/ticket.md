---
id: REQ-025
title: "Verify always-on AGS apps by unit ownership, not autostart"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-025/
branch: ticket/REQ-025-autostart-always-apps
---

# Verify always-on AGS apps by unit ownership, not autostart

## Requirement

The v0.1.38 live apply failed at
`ags_apps_units : bar : assert autostart launches the identity once under the
shared lock`. `dotfiles-assets v0.12.1` correctly removed the `ags`
(`bar`) and `notifications` launch lines from
`configs/hypr/autostart.lua`: those always-on apps are now owned by the
`dotfiles-ags-bar.service` / `dotfiles-ags-notifications.service` systemd
`--user` units (REQ-023). The installer surface verification still demanded
exactly one `--expect-instance <autostart>` occurrence for every entry with an
`autostart` field, so a correct assets cutover can never pass.

The launch policy must decide the autostart contract:

- `launch: always` — the systemd `--user` unit exists and is enabled, and the
  assets-owned autostart file contains **zero** occurrences of
  `--expect-instance <autostart>` (the always-on app is never launched by
  autostart).
- `launch: on-demand` — an entry that declares an `autostart` identity keeps
  exactly **one** occurrence through `ags-run-locked` (capture, clipboard).

Provisioning never writes the assets-owned autostart content. The `verify`
mirror must apply the same split.

## Acceptance

- [x] `ags_apps_units/tasks/_verify_surfaces.yml` asserts zero
      `--expect-instance <autostart>` occurrences for `launch: always` and the
      installed/enabled systemd unit, and exactly one `ags-run-locked`
      occurrence for `launch: on-demand`.
- [x] The failure messages and comments describe the AD-32/assets v0.12.1
      epoch: units own always-on apps, autostart owns only launch-on-login
      overlays.
- [x] The autostart stat/read/assert tasks are guardable by `app.launch`; no
      remaining assumption requires an always-on app in autostart.
- [x] The `verify` mirror (`_verify_standalone.yml`) applies the same split.
- [x] `tests/unit/test_ags_apps_units_role.py` fixtures use the actual assets
      v0.12.1 autostart shape (no `ags`/`notifications` lines) and cover:
      always zero + enabled unit passes, always with an autostart line fails,
      on-demand one occurrence passes, on-demand missing fails.
- [x] `tests/unit/test_verify_role.py` fixtures/tests cover the same branches.
- [x] `make gates`, `make ci-gates-parity`, and the targeted tests pass.
- [x] Engine `0.1.39` + CHANGELOG; annotated tag `v0.1.39` after the
      fast-forward merge; push `main` and the tag; no apply.

## Evidence / Verify

Worktree `.worktrees/REQ-025/`, branch
`ticket/REQ-025-autostart-always-apps`. Commits: `77554a5` (plan),
`44c33a9` (implementation + release metadata), plus this evidence commit.

- Failure source: `ansible/roles/ags_apps_units/tasks/_verify_surfaces.yml`
  v0.1.38 keyed the autostart assert only on `app.autostart is defined` and
  required exactly one `--expect-instance <autostart>` for every such entry.
- Assets evidence: `git -C /home/inumaki/Development/dotfiles/dotfiles-assets
  show v0.12.1:configs/hypr/autostart.lua | grep -n -- '--expect-instance'`
  → only `capture` (line 38) and `clipboard` (line 56); **zero** lines for
  `ags`/`notifications`. The checked-in fixture
  `tests/fixtures/ags-apps/autostart/v0.12.1.lua` is that verbatim content
  (renamed from the stale `v0.6.2.lua`).
- Assertion diff (`5f50662..44c33a9`):
  - `_verify_surfaces.yml` always branch:
    `(content.split('--expect-instance ' ~ app.autostart) | length - 1) == 0`
    when `app.launch == 'always'`; on-demand branch keeps `== 1` and
    `'ags-run-locked' in content` when `app.launch == 'on-demand'`.
    The old single assert was `== 1` gated only by `app.autostart is
    defined`.
  - `_one.yml` invokes `_verify_always_on_unit.yml` after render/enable for
    `launch: always`. The new file stats `ags_apps_units_unit_file` +
    `ags_apps_units_unit_wants_link`, resolves the wants link, and asserts
    `isreg` / `islnk` / target `isreg` (installed and enabled).
  - `verify/tasks/_verify_standalone.yml` mirrors the split: always `== 0`,
    on-demand `== 1`; `_verify_units.yml` still owns the static unit contract.
- Targeted tests:
  - `uv run pytest -q tests/unit/test_ags_apps_units_role.py -m "not
    integration and not container_target"` → **43 passed in 472.54s**.
    `TestAutostartLaunchPolicy` (4 cases) covers always-zero + enabled unit
    pass, always-with-line fail, on-demand-one pass, on-demand-missing fail.
  - `uv run pytest -q tests/unit/test_verify_role.py -m "not integration and
    not container_target"` → **116 passed, 15 deselected in 54.34s**.
  - `uv run pytest -q tests/unit/test_verify_role.py::TestVerifyAutostartLaunchPolicy
    -m integration` → **3 passed in 236.75s**.
  - `uv run pytest -q "tests/unit/test_verify_role.py::TestVerifyRuntime::test_verify_passes_on_a_provisioned_machine"
    -m integration` → **1 passed in 149.33s**.
- `make gates` → **rc=0**:
  - `test`: `976 passed, 3 skipped, 55 deselected in 717.74s`
  - `lint`: `All checks passed!`
  - `hermetic`: `945 passed, 34 skipped, 55 deselected in 652.33s`
  - `lock-check`: `Resolved 33 packages in 0.67ms`
  - `docs-check`: rc=0
- `make ci-gates-parity` → **PASS**:
  `gates=['docs-check','hermetic','lint','lock-check','test']`,
  CI-only exempt `assets-parity, ci-gates-parity, release`.
- Release: engine `0.1.39` in `pyproject.toml`,
  `src/provisioning/__init__.py` and `uv.lock`; annotated tag `v0.1.39`
  created on the fast-forward merge commit. `main` and the tag pushed. No
  `make apply` was run.

## Handoff (dotfiles-v3)

- Bump `dotfiles/provisioning/installer.pin` to `v0.1.39` in the next wave.
- No `dotfiles-assets` edit is needed: v0.12.1/v0.12.2 already own the correct
  always-on unit / on-demand autostart split. No `dotfiles-v3` file is edited
  by this ticket.
