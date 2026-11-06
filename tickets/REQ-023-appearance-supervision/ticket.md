---
id: REQ-023
title: "Supervise the always-on AGS apps with systemd --user units"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-023/
branch: ticket/REQ-023-appearance-supervision
---

# Supervise the always-on AGS apps with systemd --user units

## Requirement

Appearance-plane v2 (`dotfiles-v3/docs/105-appearance-plane-v2.md` §4) freezes
the always-on apps on supervision instead of raw `ags run` processes. The two
always-on entries in the single composition app list are:

| App | Unit | Instance | Config dir |
| --- | --- | --- | --- |
| bar | `dotfiles-ags-bar.service` | `ags` | `ags` |
| notifications | `dotfiles-ags-notifications.service` | `notifications` | `ags-notifications` |

The installer must be the ONE owner of those two instances. It renders and
enables the units, starts them when a live `systemd --user` manager exists, and
stops starting them through a raw wrapper path. On-demand apps
(`capture`, `clipboard`, `wallpaper-selector`, `icme`, `btop-theme-studio`)
keep their launchers and are never unit-ized.

Each unit:

```ini
[Unit]
PartOf=graphical-session.target
After=graphical-session.target

[Service]
Type=simple
ExecStart=<bin>/ags-run-locked --exec --expect-instance <instance> \
  --lock-timeout 10 --register-timeout 10 -- \
  /usr/bin/ags run -d <install>/config/<configDir>
ExecStop=/usr/bin/ags quit -i <instance>
Restart=on-failure
RestartSec=2
TimeoutStopSec=10
KillMode=mixed

[Install]
WantedBy=default.target
```

`ExecStart` uses the shared launch-lock wrapper (AD-28), then `exec`s
`/usr/bin/ags run` in the foreground so systemd tracks the real process. The
spine link `<install>/config/<configDir>` is the launch path; `configDir` and
the instance come from the composition app list, never a second list.

### Frozen RFC risks

1. **Lock-fd escape (RFC §4.1 / AD-28).** The wrapper must close its `flock`
   fd (`9>&-`) on the `exec`, or the app process inherits the lock and every
   later launch deadlocks. The existing background path already closes it; the
   new `--exec` path must do the same.
2. **Delegated exit 0.** `ags run` exits 0 when it delegates to an
   already-running instance, which would leave a `Restart=on-failure` unit
   inactive with no failure. `--exec` must pre-check the expected instance and
   exit non-zero with a named error when it is already on the bus, so a
   delegated start is a unit failure, not a silent success. The remaining race
   window is documented; the installer quiesces before it starts the unit.
3. **Never kill the `ags run` parent (RFC §4.2).** `ExecStop` is
   `/usr/bin/ags quit -i <instance>`; no script, rollback or repair path may
   `kill`/`pkill`/process-tree-kill the wrapper. `KillMode=mixed` only bounds
   the stop after the graceful exit.

## Acceptance

- [x] `ags_apps_units` renders `dotfiles-ags-bar.service` and
      `dotfiles-ags-notifications.service` from the app list into
      `~/.config/systemd/user/`, with the unit content above.
- [x] The installer enables the units and starts them when a live
      `systemctl --user` manager exists; without one it creates the
      `default.target.wants/` symlink (R-6 discipline) and verify/doctor is the
      loud check.
- [x] Always-on apps are no longer started through a raw wrapper call in the
      role; only on-demand cutover proofs keep the wrapper start. Rollback
      restarts an always-on previous instance through its unit, not a raw
      process.
- [x] `ags-run-locked` gains `--exec`: acquire the shared lock, refuse an
      already-running expected instance (non-zero), close fd 9, then exec the
      supplied command. The existing background/register-and-exit mode is
      unchanged.
- [x] On-demand apps (`capture`, `clipboard`, `wallpaper-selector`, `icme`,
      `btop-theme-studio`) keep their launchers and gain no unit.
- [x] `verify` asserts the two unit files exist, are enabled (wants symlink),
      use `ExecStop=... ags quit -i <instance>`, and name the manifest's
      `configDir`/`instance`. Live unit-active/PID/bus-owner/orphan checks are
      handed to the runtime doctor ticket (RFC §4.3), not duplicated here.
- [x] Unit-template rendering, enabled state, no-raw-duplicate-launch,
      delegated-exit guard and lock-fd handling are covered by tests/
      fixtures; README and CHANGELOG are updated.
- [x] `make gates`, `make ci-gates-parity` and the targeted unit tests pass;
      engine `0.1.37` and annotated tag `v0.1.37` land after a fast-forward
      merge; no push, no apply.

## Evidence / Verify

Branch `ticket/REQ-023-appearance-supervision`, worktree
`.worktrees/REQ-023/`. Commits: `0757c55` (plan), `6d27b23`
(implementation + release metadata).

- Unit names/template:
  `rg -n "dotfiles-ags|dotfiles-ags-app.service" ansible/roles/ags_apps_units`
  → the template renders `dotfiles-ags-{{ app.app }}.service` and the two
  app-list names are `dotfiles-ags-bar.service` /
  `dotfiles-ags-notifications.service`.
- Unit contract:
  `ansible/roles/ags_apps_units/templates/dotfiles-ags-app.service.j2:13-33`
  — `ExecStart=<bin>/ags-run-locked --exec ... -- /usr/bin/ags run -d
  {{ ags_apps_units_spine_link }}`, `ExecStop=/usr/bin/ags quit -i
  {{ app.instance }}`, `Restart=on-failure`, `RestartSec=2`,
  `TimeoutStopSec=10`, `KillMode=mixed`, `After=graphical-session.target`,
  `WantedBy=default.target`.
- Lock-fd + delegated guard:
  `ansible/roles/cli_tools/files/ags-run-locked:85-110` — `--exec` exits 1
  when `--expect-instance` is already on the bus, then `exec "$@" 9>&-`.
  Background mode still exits 0 for the existing launcher/autostart no-op.
  Timeout cleanup now quits by instance instead of killing the `ags run`
  parent.
- One owner:
  `ansible/roles/ags_apps_units/tasks/_one.yml:231-302` — always-on renders
  and enables/starts the unit; only `launch: on-demand` can take the raw
  cutover start. `_rollback.yml:87-126` restarts an always-on previous
  instance through its unit.
- Static verify:
  `ansible/roles/verify/tasks/_verify_units.yml` — asserts the unit file, the
  `default.target.wants` link, `ExecStop=... quit -i`, and the unit's config
  path/instance match the app list; no live PID/bus checks.
- Targeted tests:
  - `uv run --frozen pytest -q tests/unit/test_ags_units_supervision.py
    -m "not integration and not container_target"` → **10 passed**.
  - `uv run --frozen pytest -q tests/unit/test_ags_apps_units_role.py
    -m "not integration and not container_target"` → **39 passed**.
  - `uv run --frozen pytest -q tests/unit/test_verify_role.py
    -m "not integration and not container_target"` → **115 passed,
    12 deselected**.
  - `uv run --frozen pytest -q
    "tests/unit/test_verify_role.py::TestVerifyRuntime::test_verify_passes_on_a_provisioned_machine"
    -m integration` → **1 passed**.
- `make gates` → **rc=0**:
  - `test`: `971 passed, 3 skipped, 52 deselected in 606.44s`
  - `lint`: `All checks passed!`
  - `hermetic`: `940 passed, 34 skipped, 52 deselected in 548.11s`
  - `lock-check`: `Resolved 33 packages in 0.69ms`
  - `docs-check`: rc=0
- `make ci-gates-parity` → **PASS**
  (`gates=['docs-check','hermetic','lint','lock-check','test']`,
  exempt `assets-parity, ci-gates-parity, release`).
- Engine `0.1.37` + CHANGELOG; annotated tag `v0.1.37` created after the
  fast-forward merge. No `apply`, no push.

## Handoff

- **dotfiles-assets**: the assets-owned `configs/hypr/autostart.lua` still
  launches `ags` and `notifications` through `ags-run-locked`. The units are
  now the owner of those instances; the two always-on autostart lines must be
  removed in the assets cutover so login has one launch path. Provisioning
  never writes assets-owned autostart content. Until then the wrapper
  pre-check makes the autostart call a no-op rather than a second process.
- **dotfiles-runtime (doctor ticket)**: RFC §4.3 doctor leg — live
  `systemctl --user is-active`/`MainPID`, bus owner in the unit cgroup, orphan
  `ags run`/`gjs` detection, and graceful `--repair` via
  `systemctl --user restart` / `ags quit -i`. This ticket only checks the
  static unit contract.
- **dotfiles-v3**: bump `installer.pin` to `v0.1.37` in the wave-6 tuple bump.
