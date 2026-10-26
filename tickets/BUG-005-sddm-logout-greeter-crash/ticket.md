---
id: BUG-005
title: "Logout leaves a black VT — sddm-helper exits 1 and the greeter never restarts"
kind: bug
status: triage
lane: 4
severity: high
links:
  openspec: none
  bmad: none
worktree: .worktrees/BUG-005/
branch: ticket/BUG-005-sddm-logout-greeter-crash
repro: "In the VM: AGS bar power menu -> wlogout -> Logout (key e), which runs `loginctl terminate-user $USER`; the screen drops to a black VT with a blinking cursor and never returns to the greeter"
observed: "Boot ccd99035 (2026-10-26): `Session started true` at 14:31:34; at 14:35:11 sddm-helper is SIGTERM-killed inside session-2.scope, SDDM logs `ERROR_INTERNAL \"Process crashed\"` / `sddm-helper ... crashed (exit code 1)`; no `Greeter starting` or `Display server started` afterwards; power key at 14:36:31. The same crash appears on 8 boots from 2026-10-23 to 2026-10-26."
expected: "Logout returns to the Pixie greeter on seat0 within a sane time (< 30 s), no sddm-helper `Process crashed`, and a subsequent login succeeds; repeated 5 times."
---

# BUG-005 — Logout leaves a black VT; sddm-helper crash and no greeter restart

## Summary

Clicking **Logout** ends the Hyprland/uwsm session but never brings SDDM's
greeter back. The display stays on a black VT with a blinking cursor; the only
recovery is a short power-button press. The first login after a boot works.
This is **not** the old BUG-004 90 s bounce: there is no `Session started false`,
no `falling back to DisplayServer=x11-user`, and no `sddm-helper exited with 2`.

The recurring signature is the **user-session helper being killed while its
session scope is torn down** (`SIGTERM` by `systemd[1]`), which SDDM reports as
`ERROR_INTERNAL "Process crashed"` / exit 1. SDDM then never starts a second
greeter. Triage only: no fix is implemented here.

## Repro

GUI path (exact user action):

1. Log in to Hyprland through SDDM (the `hyprland-uwsm.desktop` session).
2. Click the AGS bar power menu, then the wlogout **Logout** tile (or press `e`).
   AGS execs `wlogout` (`ags-apps/bar/bar/widgets/power-menu.tsx:18`), and the
   tile's action is `loginctl terminate-user $USER`
   (`dotfiles-assets/configs/wlogout/layout:14-17`; deployed copy
   `/home/inumaki/.config/wlogout/layout:14-17`).
3. Observe: the session stops, the screen drops to a black VT with a blinking
   cursor, and no greeter returns. A short power-button press is required.

Non-GUI equivalent (VM only — **do not run on the host**):

```sh
loginctl terminate-user "$USER"
```

Supporting read-only evidence commands (safe on the host):

```sh
journalctl -b -1 -u sddm --no-pager -o short-precise
journalctl -b -1 --no-pager -o short-precise --since '2026-10-26 14:35:05' --until '2026-10-26 14:35:16'
coredumpctl list sddm-helper --no-pager
journalctl --no-pager -o short-precise --grep 'Auth: sddm-helper.*crashed \(exit code 1\)'
```

Evidence: the commands above reproduce the log signature on the captured boot;
the GUI action is documented at `ags-apps/bar/bar/widgets/power-menu.tsx:18` and
`dotfiles-assets/configs/wlogout/layout:14-17`.
Verify: `journalctl -b -1 -u sddm --no-pager | grep -E 'Session started true|Process crashed|exited with 1'`.

## Observed

### Captured boot (previous boot, local time -05)

Boots (`journalctl --list-boots`):

```text
-1 ccd99035ee63446bb6493da9a6cfb82b  Mon 2026-10-26 14:31:14 -> 14:36:32
 0 6b5a275355244e7290987b5275fc087a  Mon 2026-10-26 14:37:36 -> current
```

`sddm` log on boot `ccd99035…`:

```text
14:31:21.512486  Started Simple Desktop Display Manager.
14:31:21.556868  Display server started.
14:31:21.557724  Greeter starting...
14:31:21.686617  Greeter session started successfully
14:31:21.689539  sddm-helper-start-wayland[1067]: Starting Wayland process "weston --shell=kiosk" "sddm"
14:31:34.229385  Message received from greeter: Login
14:31:34.232053  Session "/usr/share/wayland-sessions/hyprland-uwsm.desktop" selected, command: "uwsm start -e -D Hyprland hyprland.desktop" for VT 2
14:31:34.354005  Greeter stopped. SDDM::Auth::HELPER_SUCCESS
14:31:34.453131  Session started true
14:35:11.707710  Authentication error: SDDM::Auth::ERROR_INTERNAL "Process crashed"
14:35:11.707720  Auth: sddm-helper (--socket /tmp/sddm-auth-1ac98bba-abae-4a86-b150-2a7efa0e5b66 --id 1 --start uwsm start -e -D Hyprland hyprland.desktop --user inumaki) crashed (exit code 1)
14:35:11.707725  Auth: sddm-helper exited with 1
14:36:31.991908  Signal received: SIGTERM   # short power-button press
14:36:31.991918  Stopping Simple Desktop Display Manager...
14:36:32.010246  sddm.service: Deactivated successfully.
```

The session had been up 3 m 37 s. **Nothing** between 14:35:11 and 14:36:31
starts another greeter or display server.

The system journal shows what happened immediately before the `sddm` error:

```text
14:35:11.706771  systemd[1]: session-2.scope: Killing process 1455 (sddm-helper) with signal SIGTERM.
14:35:11.706811  systemd[1]: session-2.scope: Killing process 1515 (sh) with signal SIGTERM.
14:35:11.706846  systemd[1]: session-2.scope: Killing process 1545 (systemctl) with signal SIGTERM.
14:35:11.707031  systemd[1]: Stopping Session 2 of User inumaki...
14:35:11.707201  uwsm[1515]: Received SIGHUP, stopping wayland-session-envelope@hyprland.desktop.target...
14:35:11.707495  uwsm[1515]: PID 1545 exited with RC 129
14:35:11.707710  sddm[1014]: Authentication error: SDDM::Auth::ERROR_INTERNAL "Process crashed"
14:35:14.981900  systemd-logind[904]: Removed session 2.
14:35:15.427353  systemd-logind[904]: Removed session 3.
14:35:15.427375  (sd-pam)[1503]: pam_unix(systemd-user:session): session closed for user inumaki
14:36:31.978151  systemd-logind[904]: Power key pressed short.
14:36:31.979094  systemd-logind[904]: System is powering down.
```

Session 2 is the graphical user session; session 3 is the user manager
(`New session '3' of user 'inumaki' with class 'manager'` at 14:31:34.369073).
Both were removed, and the user manager's PAM session closed — consistent with
**terminating every session of the user**, not just the graphical session
(a single-session end leaves the user manager running). This is an inference
from the log ordering; confirm the exact `loginctl` call in the VM (H1).

Current boot (`6b5a2753…`) first login is clean:

```text
14:37:57.759468  Message received from greeter: Login
14:37:57.980065  Session started true
```

No `Process crashed` line exists on the current boot yet because no logout has
been attempted.

### Recurrence

`journalctl --grep 'Auth: sddm-helper.*crashed \(exit code 1\)'` shows the same
user-session helper crash on **8 boots** (all local -05):

| Crash timestamp (local -05) | Event |
| --- | --- |
| 2026-10-23 17:44:47 | user-session helper exit 1 |
| 2026-10-24 21:03:58 | user-session helper exit 1 |
| 2026-10-25 18:31:24 | user-session helper exit 1 |
| 2026-10-25 22:17:28 | user-session helper exit 1 |
| 2026-10-26 08:28:00 | user-session helper exit 1 |
| 2026-10-26 14:17:17 | user-session helper exit 1 |
| 2026-10-26 14:27:46 | user-session helper exit 1 |
| 2026-10-26 14:35:11 | user-session helper exit 1 |

The same signature appears on every captured logout attempt in this window, so
the failure is deterministic, not a one-off race.

### Not a coredump

`coredumpctl list sddm-helper --no-pager` → `No coredumps found.` The helper's
exit 1 is a signal-driven termination path, not a segfault. Do not expect a core
file to explain it.

Evidence: journal excerpts above are from
`journalctl -b -1 -u sddm --no-pager -o short-precise` and
`journalctl -b -1 --no-pager -o short-precise`; recurrence from
`journalctl --no-pager -o short-precise --grep 'Auth: sddm-helper.*crashed \(exit code 1\)'`;
coredump from `coredumpctl list sddm-helper --no-pager`.
Verify: `journalctl -b -1 -u sddm --no-pager | grep -nE 'Session started true|Process crashed|exited with 1|Greeter starting'`.

## Expected

- After Logout, SDDM tears the user session down cleanly and **restarts the
  Pixie/Wayland greeter on seat0**; the greeter appears within a sane time
  (target < 30 s).
- `sddm` logs a second `Greeter starting...` / `Greeter session started
  successfully` and no `ERROR_INTERNAL "Process crashed"` for the user-session
  helper.
- A subsequent login succeeds; the cycle works **5 times in a row**
  (the session acceptance).
- No power-button recovery is needed.

## Hypotheses (verify, do not assume)

### H1 — The wlogout logout action is a forceful user teardown (primary)

`dotfiles-assets/configs/wlogout/layout:14-17` defines Logout as
`loginctl terminate-user $USER`. The journal shows **both** the graphical
session (2) and the user-manager session (3) removed, plus the user's PAM
session closed. `loginctl terminate-session $XDG_SESSION_ID`, `uwsm stop`, or
`hyprctl dispatch exit` might end only the graphical session and leave SDDM able
to restart the greeter.

Evidence: `dotfiles-assets/configs/wlogout/layout:15`; boot `ccd99035…` log
lines at 14:35:11.707031 (`Stopping Session 2`), 14:35:14.981900
(`Removed session 2`), 14:35:15.427353 (`Removed session 3`).
Verify: `sed -n '14,17p' dotfiles-assets/configs/wlogout/layout` and
`journalctl -b -1 --no-pager | grep -E 'Stopping Session 2|Removed session [23]'`.

### H2 — The Wayland greeter/weston never restarts

The greeter is a weston kiosk client (`CompositorCommand=weston --shell=kiosk`).
After `Greeter stopped` at 14:31:34 there is no second weston start, no second
`Greeter starting`, and no second `Display server started`. The VT/DRM state may
be wedged after the user session releases the GPU, or SDDM may never ask weston
to start again.

Evidence: boot `ccd99035…` has exactly one
`sddm-helper-start-wayland: Starting Wayland process "weston --shell=kiosk"` at
14:31:21.689539 and one `Greeter stopped` at 14:31:34.354005; no greeter/weston
lines after 14:35:11.
Verify: `journalctl -b -1 --no-pager | grep -nE 'weston|Greeter starting|Display server started'`.

### H3 — sddm-helper / uwsm / PAM teardown crash (primary)

`systemd[1]` SIGTERM-kills `sddm-helper` (PID 1455) as part of
`session-2.scope`. The helper responds with exit 1; SDDM reports
`ERROR_INTERNAL "Process crashed"` instead of a clean session end. uwsm also
receives SIGHUP and stops the envelope, and `PID 1545 (systemctl)` exits 129.
The open question is why a killed helper leaves SDDM unable to start the next
greeter: helper exit-code handling, SDDM state-machine recovery, or the PAM
session teardown.

Evidence: journal lines 14:35:11.706771–14:35:11.707725 above; no coredump; the
helper is in the session scope, so logind's teardown signal reaches it before
SDDM's own session-end handling can complete.
Verify: `journalctl -b -1 --no-pager -o short-precise --since '2026-10-26 14:35:11' --until '2026-10-26 14:35:12'`.

### H4 — Pixie login-timeout patch (secondary)

The role replaces Pixie's `interval: 5000` with `interval: 0`
(`ansible/roles/display_manager/tasks/main.yml:107-114`) and sets
`[Greeter] SessionTimeout=0`. This could affect a **restarted** greeter, but the
failure state is a bare VT cursor with no greeter process — the theme is not
even on screen. Treat as secondary until H1–H3 are ruled out; do not modify the
Pixie patch in this ticket.

Evidence: deployed `/usr/share/sddm/themes/pixie/Main.qml:83` is `interval: 0`;
`/etc/sddm.conf.d/10-dotfiles.conf` has `SessionTimeout=0`; the failing boot log
shows no `Loading file:///…/Main.qml` after 14:31:22.
Verify: `grep -n 'interval' /usr/share/sddm/themes/pixie/Main.qml | head` and
`grep -n 'SessionTimeout' /etc/sddm.conf.d/10-dotfiles.conf`.

## Investigation plan (next session, self-contained)

Do **not** reproduce on the host: every logout currently costs a power cycle.
Use the Incus VM from `dotfiles-v3` (`make vm-up` / `make vm-fresh`; sudo is a
user-run step) or an equivalent disposable VM with the same SDDM + weston +
Pixie + uwsm stack.

### 1. Capture the failing boot evidence (host, read-only)

```sh
journalctl -b -1 -o short-precise > /tmp/bug-005/journal-boot--1.log
journalctl -b -1 -u sddm -o short-precise > /tmp/bug-005/sddm-boot--1.log
journalctl --user -b -1 -o short-precise > /tmp/bug-005/user-boot--1.log
coredumpctl list sddm-helper --no-pager > /tmp/bug-005/coredump-sddm-helper.log
journalctl -b -1 --no-pager | grep -iE 'weston|sddm|uwsm|logind|pam|drm|vt' \
  > /tmp/bug-005/layer-attribution.log
```

Answer from the capture:

- Which process requested the session teardown? (`loginctl` does not log the
  caller by default; check `auditd` if enabled, the wlogout invocation, and the
  exact logind ordering.)
- Did SDDM receive a session-finished event? Did it try to start a greeter
  (look for `Greeter starting`, `Display server started`, weston output)?
- Did `sddm-helper` log PAM close before it died, or was it killed mid-teardown?
- Is session 3 (user manager) always removed? That distinguishes
  `terminate-user` from `terminate-session`.

### 2. Graceful-vs-forceful logout matrix (VM only)

Take a VM snapshot, then in one graphical session run each action separately,
recording `journalctl -b -u sddm` and whether the greeter returns:

| Case | Command | What it proves |
| --- | --- | --- |
| Forceful user | `loginctl terminate-user "$USER"` | reproduces the wlogout action (H1) |
| Graceful session | `loginctl terminate-session "$XDG_SESSION_ID"` | session-only teardown; does the greeter return? |
| uwsm stop | `uwsm stop` | uwsm's own clean shutdown path |
| Compositor exit | `hyprctl dispatch exit` | compositor-initiated exit without logind kill |

For each case record: time to greeter, `Greeter starting` present/absent,
`sddm-helper` exit status, session 2/3 removal, weston start/stop. If
`terminate-session` returns to the greeter but `terminate-user` does not, the
trigger is the wlogout action (**H1**) and the fix belongs in
`dotfiles-assets`. If every case leaves the VT black with helper exit 1, the
defect is in the SDDM/uwsm/PAM teardown (**H3**), not the logout tile.

### 3. Layer attribution

- **wlogout/assets layer** — `dotfiles-assets/configs/wlogout/layout` (Logout
  action) and the deployed copy. Fix candidate: a graceful action
  (`loginctl terminate-session "$XDG_SESSION_ID"` or `uwsm stop`), verified in
  the VM.
- **uwsm/session layer** — `dotfiles-v3` manifests (`dotfiles/provisioning/*.yaml`),
  the `uwsm` package pin, and the `hyprland-uwsm.desktop` session. Fix candidate:
  session unit ordering / helper exit handling.
- **provision layer** — `ansible/roles/display_manager` (SDDM config, weston
  package, Pixie pin/patch, verify assertions) and the assets
  `templates/display-manager/sddm.conf.j2`.
- **ags-apps layer** — only launches `wlogout`; it does not choose the action.

A fix is not assumed to be in `dotfiles-provision`. If the root cause is the
wlogout action, open a ticket in `dotfiles-assets` per its AGENTS/worktree
rules and cross-link BUG-005. If it is the uwsm/session integration, open a
ticket in `dotfiles-v3`. Only the SDDM config/weston/Pixie part belongs here.

### 4. Acceptance

- Logout returns to the Pixie greeter on seat0 within 30 s; no
  `ERROR_INTERNAL "Process crashed"` for the user-session helper.
- A subsequent login succeeds; repeat **5 times**.
- `python3 scripts/check-session-bounce.py --since "<start>"` (from
  `dotfiles-v3`) stays green across the five cycles.
- VM regression: a scripted logout/login loop with the same assertions; no host
  logout needed for CI.

## Cross-repo pointers

- `dotfiles-assets/configs/wlogout/layout:14-17` — the Logout action
  (`loginctl terminate-user $USER`). This is the most likely trigger; per
  `dotfiles-assets/AGENTS.md` any fix there needs its own ticket/worktree.
- `dotfiles-v3/dotfiles/provisioning/` — manifests that pin the installer and
  `uwsm`; `dev/README.md` §Host 5-login acceptance and
  `scripts/check-session-bounce.py`; `dev/vm-session-loop.sh` for VM repros.
  Note: as read on 2026-10-26, `dotfiles-v3/dotfiles/` contains only
  `provisioning/` manifests — there is no uwsm/session/autostart file there.
  The Hyprland startup block is `dotfiles-assets/configs/hypr/autostart.lua`
  (deployed as `~/.config/hypr/autostart.lua`), and
  `/usr/share/wayland-sessions/hyprland-uwsm.desktop` is package-provided
  (`Exec=uwsm start -e -D Hyprland hyprland.desktop`). Check the deployed
  config/package before attributing a session-layer cause to v3.
- `ags-apps/bar/bar/widgets/power-menu.tsx:18` — the bar button just execs
  `wlogout`; the action lives in the assets layout.
- `dotfiles-provision` — SDDM config (`display_manager` role), weston package,
  Pixie pin/timeout patch, and `verify` assertions. Only this layer is owned by
  the current ticket.

## Blocked acceptance

The **5-login session acceptance** is blocked by this bug. Every logout
currently ends on a black VT and requires a power cycle, so five logout/login
cycles cannot be completed. Do not mark the session work fully accepted until
BUG-005 is fixed and the five-cycle acceptance passes. This also affects the
BUG-004 closeout's “5 logins” evidence: first login is fine, but the
logout→greeter→login loop is not.

## Triage

- **kind: bug** — repro/observed/expected are present; the failure is executable
  evidence from the captured boot and is deterministic across 8 boots.
- **lane: 4 (bmad-advisory)** — the root cause is not yet attributed; four
  candidate layers (wlogout/assets, weston greeter, sddm-helper/uwsm/PAM,
  Pixie) span three repos. This needs exploration before a spec/change; the
  normal bug flow (`triage → in-progress → done`) and regression test still
  apply. If the investigation collapses the cause to one bounded role/config
  edit, re-triage to lane 2/3 before implementation.
- **severity: high** — every logout loses the graphical session and requires a
  hard power cycle; no data loss, but the machine is not usable across
  logins and the session acceptance is blocked.

Evidence: the repro/observed/expected front matter and the journal excerpts
above; the cross-repo paths are quoted with line numbers.
Verify: `rg -n '^kind: bug|^status: triage|^lane: 4|^severity: high' tickets/BUG-005-sddm-logout-greeter-crash/ticket.md`.

## Done-when

- [ ] Root cause attributed to a layer with captured VM/host evidence.
- [ ] The identified repo has its own ticket if the fix is outside
      `dotfiles-provision` (assets/v3), cross-linked here.
- [ ] Logout returns to the greeter; a subsequent login works, 5 times.
- [ ] Regression test/check covers the logout→greeter path.
- [ ] `make gates` green on the implementation commit; docs/ticket updated.
