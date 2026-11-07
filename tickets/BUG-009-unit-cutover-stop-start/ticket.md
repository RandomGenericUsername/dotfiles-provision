---
id: BUG-009
title: "v3 cutover leaves always-on AGS units on the previous tag (state: started is a no-op)"
kind: bug
status: in-progress
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

`ags_apps_units/tasks/_one.yml` quiesces every app with `ags quit` and
`tasks/_quiesce.yml` waits for the D-Bus name to release, but it never stops the
owning systemd `--user` unit for `launch: always` apps. The unit remains active
(or is restarted by `Restart=on-failure` from the still-old link) while the
spine/XDG links are repointed. The later `ansible.builtin.systemd` task uses
`state: started`, which is a no-op for an already-active unit, so the old
process keeps the bus name. On-demand apps are unaffected because they are
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

- [ ] `_quiesce.yml` stops an existing always-on unit under the shared launch
      lock and fails when the unit stays active or the stop times out.
- [ ] After the link repoint, `_one.yml` explicitly runs
      `systemctl --user start <unit>` and fails if the unit was already active
      before that start or is not active with a main PID after it.
- [ ] Manager-less hosts keep the `default.target.wants` enablement path and
      are not asked to run `systemctl`.
- [ ] The app loop covers `bar` and `notifications`; a simulated active-unit tag
      bump proves stop → relink → start order and that the start resolves the
      new link target.
- [ ] Tests cover active-unit order, inactive/manager-less, failed start, stop
      timeout, no raw always-on launch, and unchanged on-demand behaviour.
- [ ] `make gates`, `make ci-gates-parity` and the targeted AGS/verify suites
      pass.
- [ ] Engine `0.1.45` + CHANGELOG, annotated tag `v0.1.45` after the
      fast-forward merge; push `main` and the tag; no apply.

## Non-goals

- No live apply is run here.
- No composition, runtime, assets or app tag is changed.

## Evidence / Verify

Filled in the implementation commit and this ticket's evidence update.
