---
id: BUG-009
title: "v3 cutover leaves always-on AGS units on the previous tag (state: started is a no-op)"
kind: bug
status: done
lane: 2
severity: high
links:
  openspec: none
  bmad: none
worktree: .worktrees/BUG-009/
branch: ticket/BUG-009-unit-cutover-stop-start
repro: "On a host running v0.1.44 with dotfiles-ags-notifications.service active on notifications v0.4.0, run the v3 cutover apply that pins notifications v0.5.0 (the composition manifests at the v3 generation)."
observed: "The apply log shows notifications quiesce succeeded (bus name released), the tag was cloned and the spine/XDG links were repointed to v0.5.0, but `systemd : notifications : reload, enable and start the always-on unit` returned ok (unchanged). The unit was still active with the old process, so verify failed `notifications : assert the live appearance-refresh handler answered` with `unknown request: appearance-refresh 000…` — the running instance was still v0.4.0."
expected: "An always-on cutover stops dotfiles-ags-<app>.service first (ExecStop=ags quit), waits for the unit to leave active and the bus name to release, repoints the links, then explicitly starts the unit. Verify must reach the new process, and the same stop/relink/start path must cover dotfiles-ags-bar.service."
---

# BUG-009 — v3 cutover leaves always-on AGS units on the previous tag

## Root cause

`ags_apps_units/tasks/_one.yml` quiesced every app with `ags quit` and
`tasks/_quiesce.yml` waited for the D-Bus name to release, but it never stopped
the owning systemd `--user` unit for `launch: always` apps. The unit could be
restarted by `Restart=on-failure` from the still-old link while the spine/XDG
links were repointed. The later `ansible.builtin.systemd` task used
`state: started`, which is a no-op for an already-active unit, so the old
process kept the bus name. On-demand apps are unaffected because they are
started through the launch lock after the repoint.

## Repro

On a host running v0.1.44 with `dotfiles-ags-notifications.service` active on
notifications `v0.4.0`, run the v3 cutover apply that pins notifications
`v0.5.0` (the composition manifests at the v3 generation).

## Observed

The apply log shows notifications quiesce succeeded (bus name released), the tag
was cloned and the spine/XDG links were repointed to `v0.5.0`, but
`systemd : notifications : reload, enable and start the always-on unit`
returned ok (unchanged). The unit was still active with the old process, so
verify failed `notifications : assert the live appearance-refresh handler
answered` with `unknown request: appearance-refresh 000…` — the running
instance was still `v0.4.0`.

## Expected

An always-on cutover stops `dotfiles-ags-<app>.service` first
(`ExecStop=ags quit`), waits for the unit to leave active and the bus name to
release, repoints the links, then explicitly starts the unit. Verify must reach
the new process, and the same stop/relink/start path must cover
`dotfiles-ags-bar.service`.

## Acceptance

- [x] `_quiesce.yml` stops an existing always-on unit under the shared launch
      lock and fails when the unit stays active or the stop times out.
- [x] After the link repoint, `_one.yml` explicitly runs
      `systemctl --user start <unit>` and fails if the unit was already active
      before that start or is not active with a main PID after it.
- [x] Manager-less hosts keep the `default.target.wants` enablement path and
      are not asked to run `systemctl`.
- [x] The app loop covers `bar` and `notifications`; a simulated active-unit tag
      bump proves stop → relink → start order and that the start resolves the
      new link target.
- [x] Tests cover active-unit order, inactive/manager-less, failed start, stop
      timeout, no raw always-on launch, and unchanged on-demand behaviour.
- [x] `make gates`, `make ci-gates-parity` and the targeted AGS/verify suites
      pass.
- [x] Engine `0.1.45` + CHANGELOG, annotated tag `v0.1.45` after the
      fast-forward merge; push `main` and the tag; no apply.

## Non-goals

- No live apply is run here.
- No composition, runtime, assets or app tag is changed.

## Evidence / Verify

Worktree `.worktrees/BUG-009/`, branch
`ticket/BUG-009-unit-cutover-stop-start`. Commits: `7315b42` (plan),
`de03260` (fix + release metadata), plus this evidence commit. Annotated tag
`v0.1.45` created on the fast-forward merge commit; no apply was run.

### Exact command sequence for `launch: always`

Pre-cutover, inside `_quiesce.yml` under the shared `flock`
(`ansible/roles/ags_apps_units/tasks/_quiesce.yml:38-61`):

1. `systemctl --user stop "$AGS_UNIT"` — runs
   `ExecStop=/usr/bin/ags quit -i <instance>` from the unit.
2. Bounded `systemctl --user is-active --quiet "$AGS_UNIT"` (40 × 0.25 s)
   until the unit is not active; otherwise
   `AGS unit '<unit>' stayed active after systemctl --user stop` and exit 1.
3. `ags quit -i "$AGS_INSTANCE"` — idempotent fallback.
4. Bounded `ags list | grep -qx "$AGS_INSTANCE"` until the D-Bus name is
   released.

Then the spine/XDG/bin/launcher links are repointed. After the unit is
re-rendered (`ansible/roles/ags_apps_units/tasks/_one.yml:302-412`):

5. `systemctl --user daemon-reload`
6. `systemctl --user enable "$AGS_UNIT"`
7. `systemctl --user is-active --quiet "$AGS_UNIT"` — must be non-zero
   (refuse an already-active unit; `state: started` would be a no-op).
8. `systemctl --user start "$AGS_UNIT"`
9. `systemctl --user show --property=ActiveState --property=MainPID --value
   "$AGS_UNIT"` — assert `active` and a positive main PID.

The same path covers `dotfiles-ags-bar.service` and
`dotfiles-ags-notifications.service`; the manager-less path keeps the
`default.target.wants` symlink (`_one.yml:414-421`).

### Evidence

- `rg -n "systemctl --user (stop|start|is-active|show|enable|daemon-reload)|flock -w|ags quit -i|stayed active" ansible/roles/ags_apps_units/tasks/_quiesce.yml ansible/roles/ags_apps_units/tasks/_one.yml`
  → stop/`is-active`/`ags quit` at `_quiesce.yml:38-58`; explicit start and
  state assertions at `_one.yml:302-412`.
- Full AGS/verify unit suites:
  `uv run --frozen pytest -q tests/unit/test_ags_apps_units_role.py
  tests/unit/test_ags_units_supervision.py -m "not integration and not
  container_target"` → **63 passed in 798.60s**. This includes:
  - `test_active_unit_cutover_stops_old_link_then_starts_new_link` — first
    install starts an inactive unit; the v0.6.0→v0.2.0 bump logs
    `stop dotfiles-ags-bar.service link=<v0.6.0>` before
    `start dotfiles-ags-bar.service link=<v0.2.0> state=inactive`.
  - `test_failed_always_on_start_fails_the_cutover` — a failed
    `systemctl --user start` fails the role with
    `assert the explicit start brought the new unit up`.
  - `test_stop_timeout_fails_before_any_install` — a stop that returns 0 but
    leaves the unit active fails the bounded wait before cloning/relinking.
  - the existing manager-less full-topology test still proves the wants-link
    path and that no always-on instance is raw-started.
- Targeted BUG-009 tests:
  `... -k "active_unit_cutover or failed_always_on_start or stop_timeout or
  managerless or quiesce_stops or failed_start or refuses_an_already_active or
  renders_enables"` → **9 passed in 67.11s**.
- Verify/platform/v3 locality:
  `uv run --frozen pytest -q tests/unit/test_ags_platform_role.py
  tests/unit/test_verify_role.py tests/unit/test_v3_locality.py
  -m "not integration and not container_target"` → **150 passed,
  15 deselected in 122.15s**.
- `make gates` → all five gates pass:
  - `test`: `1004 passed, 3 skipped, 55 deselected in 1109.86s`
  - `lint`: `All checks passed!`
  - `hermetic`: `973 passed, 34 skipped, 55 deselected in 1047.24s`
  - `lock-check`: `Resolved 33 packages in 0.69ms`
  - `docs-check`: rc 0
- `make ci-gates-parity` → **PASS**
  `gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test']`;
  CI-only exempt `assets-parity, ci-gates-parity, release`.

### Verify

```
uv run --frozen pytest -q tests/unit/test_ags_apps_units_role.py \
  -k "active_unit_cutover or failed_always_on_start or stop_timeout" \
  -m "not integration and not container_target"
```
