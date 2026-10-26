# BUG-005 attribution — logout leaves a black VT

**Date:** 2026-10-26
**Status:** root cause attributed; **no fix implemented**; VM confirmation
matrix pending.
**Scope:** read-only host journal and upstream source. No host logout, no VM
run, no `sudo`, and no wlogout/Pixie/SDDM edits.

## Verdict

The failure is a two-part interaction:

1. **Trigger — the wlogout Logout tile is a forceful user teardown.** It runs
   `loginctl terminate-user $USER` (`dotfiles-assets/configs/wlogout/layout:14-17`;
   deployed copy `/home/inumaki/.config/wlogout/layout:14-17`). That ends
   **every** session of the user — the graphical session and the systemd user
   manager — not the session's normal logout.
2. **Failure mode — SDDM 0.21.0 misreads the killed helper as an
   authentication error and skips the greeter restart.** logind stops the
   session scope with `KillSignal=SIGTERM` and `SendSIGHUP=yes`; the helper
   catches SIGTERM but not SIGHUP, so SIGHUP kills it. Qt reports `CrashExit`
   with exit code 1 (the signal number). SDDM casts that 1 to
   `Auth::HELPER_AUTH_ERROR`; `Display::slotHelperFinished()` deliberately does
   **not** call `stop()` for that status. Because the greeter was already
   stopped after login, the VT is left with no compositor and no greeter:
   black VT plus cursor.

This is exactly upstream SDDM issue
[#1908](https://github.com/sddm/sddm/issues/1908); the upstream fix is open as
PR [#2103](https://github.com/sddm/sddm/pull/2103) and is not in 0.21.0. The
provision SDDM/weston/Pixie configuration is not the cause. The controllable
trigger in this stack is the wlogout action.

## Proven mechanism

### 1. What the captured boot shows

Boot `ccd99035ee63446bb6493da9a6cfb82b` (local time -05):

| Time | Event |
| --- | --- |
| 14:31:21.556868 | `Display server started.` |
| 14:31:21.557724 | `Greeter starting...` |
| 14:31:34.354005 | `Greeter stopped. SDDM::Auth::HELPER_SUCCESS` |
| 14:31:34.453131 | `Session started true` |
| 14:35:11.706771 | `systemd[1]: session-2.scope: Killing process 1455 (sddm-helper) with signal SIGTERM.` |
| 14:35:11.707720 | `Auth: sddm-helper (...) crashed (exit code 1)` |
| 14:35:11.707725 | `Auth: sddm-helper exited with 1` |
| 14:35:14.981900 | `Removed session 2.` |
| 14:35:15.427353 | `Removed session 3.` |
| 14:36:31.991908 | `Signal received: SIGTERM` (user's power key) |

There is no `Adding new display...`, `Removing display...`, second
`Display server started.`, second `Greeter starting...`, or weston start after
14:35:11. `sddm` stays active; the VT is black with a cursor.

Evidence:
`journalctl -b -1 -u sddm --no-pager -o short-precise` and
`journalctl -b -1 --no-pager -o short-precise --since '2026-10-26 14:35:11'
--until '2026-10-26 14:35:16'`.
Verify:
`journalctl -b -1 -u sddm --no-pager | grep -nE 'Display server started|Greeter starting|Process crashed|exited with|Adding new display|Removing display'`.

### 2. The wlogout action is a user-wide forceful teardown

`terminate-user` ends all sessions of the user. The journal shows both
session 2 (graphical, `Class=user`) and session 3 (`Class=manager`) removed,
plus `pam_unix(systemd-user:session): session closed` for the user manager. A
session-only teardown leaves the manager running. This matches the wlogout
command and not `uwsm stop` / `hyprctl dispatch exit`.

Evidence: `dotfiles-assets/configs/wlogout/layout:14-17`; boot log lines at
14:35:14.981900 (`Removed session 2`) and 14:35:15.427353
(`Removed session 3`); `loginctl show-session 2 -p Class -p Scope -p Leader`.
Verify:
`sed -n '14,17p' dotfiles-assets/configs/wlogout/layout` and
`journalctl -b -1 --no-pager | grep -E 'Stopping Session|Removed session|session closed for user'`.

### 3. systemd sends SIGHUP as well as SIGTERM to the session scope

Live host, current boot:

```text
$ systemctl show session-2.scope -p KillMode -p KillSignal -p SendSIGHUP
KillMode=control-group
KillSignal=15
SendSIGHUP=yes

$ grep -E 'SigCgt|SigIgn' /proc/<sddm-helper>/status
SigIgn: 0000000000001000
SigCgt: 0000000000014002    # caught: 2 (INT), 15 (TERM), 17 (CHLD); not 1 (HUP)
```

systemd v262 `src/login/logind-dbus.c:4517-4521` sets `SendSIGHUP=true` on
every login session scope, with the comment:

> Make sure that the session shells are terminated with SIGHUP since bash and
> friends tend to ignore SIGTERM

`SendSIGHUP=` sends SIGHUP immediately after the signal configured with
`KillSignal=` (`man 5 systemd.kill`). SDDM's helper only connects
`sigtermReceived` (`src/helper/HelperApp.cpp:55-58`); it installs no SIGHUP
handler. The journal's `uwsm[1515]: Received SIGHUP, stopping
wayland-session-envelope@…target` at 14:35:11.707201 confirms SIGHUP delivery
to the scope; the helper's own `Signal received: SIGTERM` line is absent
because SIGHUP's default action killed it before Qt could dispatch the SIGTERM
notifier.

Evidence: `systemctl show session-2.scope`; `/proc/<helper>/status`;
`journalctl -b -1` lines 14:35:11.706771-14:35:11.707201.
Verify:
`systemctl show session-2.scope -p KillMode -p KillSignal -p SendSIGHUP` and
`h=$(pgrep -f 'sddm-helper.*--start' | head -1); grep -E 'SigCgt|SigIgn' /proc/$h/status`.

### 4. Qt and SDDM turn signal 1 into `HELPER_AUTH_ERROR`

- Qt 6.12 `src/3rdparty/forkfd/forkfd.c:252-258` stores `WTERMSIG(status)` when
  the child is signaled; `src/corelib/io/qprocess_unix.cpp:1328-1329` copies
  that value into `exitCode` and sets `CrashExit`.
- SDDM 0.21.0 `src/auth/Auth.cpp:220-233`:
  - on `exitStatus != NormalExit`, it logs
    `crashed (exit code %d)` with `HelperExitStatus(exitStatus)`. For
    `CrashExit` that value is **1 regardless of the actual code** — this is the
    misleading `(exit code 1)` in the journal;
  - the next line prints the real code (`exited with 1`);
  - it then emits `finished((Auth::HelperExitStatus) exitCode)`.
    `HELPER_SUCCESS=0`, `HELPER_AUTH_ERROR=1`
    (`src/auth/Auth.h:84-89`). Signal 1 (SIGHUP) therefore aliases exactly the
    auth-error value.
- `src/daemon/Display.cpp:524-532` calls `stop()` only when
  `status != Auth::HELPER_AUTH_ERROR`. Status 1 suppresses the restart. Only
  signal number 1 aliases the auth-error value; a SIGTERM (15) or SIGKILL (9)
  death would have hit the restart branch. The deterministic SIGHUP from the
  session scope is what makes this failure repeat on every logout.
- The normal restart path is `Display::stop()` → `emit stopped()`
  (`src/daemon/Display.cpp:293-316`) → `Seat::displayStopped()` →
  `removeDisplay()` / `createDisplay()` (`src/daemon/Seat.cpp:112-129`), which
  is what starts weston and a new greeter. It never runs here.

Evidence: SDDM v0.21.0 sources at
<https://github.com/sddm/sddm/tree/v0.21.0>; Qt v6.12.0 sources at
<https://github.com/qt/qtbase/tree/v6.12.0>.
Verify:
`curl -fsSL https://raw.githubusercontent.com/sddm/sddm/v0.21.0/src/daemon/Display.cpp | sed -n '524,532p'`
and
`curl -fsSL https://raw.githubusercontent.com/sddm/sddm/v0.21.0/src/auth/Auth.cpp | sed -n '220,233p'`.

### 5. The greeter was already gone, so the VT is empty

At login, the greeter's helper exits cleanly
(`Greeter stopped. SDDM::Auth::HELPER_SUCCESS`, 14:31:34.354005), and
`Display::slotSessionStarted()` also schedules `m_greeter->stop()` five seconds
after success (`src/daemon/Display.cpp:545-549`). SDDM keeps
`Display::m_started=true`, so a `stop()` would still tear down and recreate the
display — but the `HELPER_AUTH_ERROR` branch skips it. The kernel VT is left
after the Hyprland/weston teardown with no greeter on it.

Evidence: boot `ccd99035…` sddm log; no `Loading file:///…/Main.qml` or
`Greeter starting...` after 14:31:34.354005.
Verify:
`journalctl -b -1 -u sddm --no-pager | grep -nE 'Greeter stopped|Session started true|Greeter starting'`.

### 6. The intended clean path

On a normal session end the compositor exits first; `uwsm`'s
`signal-handler.sh` waits for
`systemctl --user start --wait wayland-session-envelope@…target` and exits with
that return code (`/usr/lib/uwsm/signal-handler.sh:28-60`). `uwsm start` (the
helper's child) exits 0; `UserSession::finished(0)` →
`HelperApp::exit(0)` (`src/helper/UserSession.cpp:50,146-161`;
`src/helper/HelperApp.cpp:196-197`). SDDM logs
`Auth: sddm-helper exited successfully` and takes `HELPER_SUCCESS` →
`Display::stop()` → `Seat::displayStopped()` → new weston/Pixie greeter.

`uwsm stop` requests exactly the compositor unit stop and waits for the job
(`/usr/share/uwsm/modules/uwsm/main.py:4426-4465`); `hyprctl dispatch exit` is
the compositor-driven equivalent. Both are **expected** to keep the helper's
exit normal; the VM matrix proves it.

Evidence: the uwsm/helper source paths above; `uwsm stop -h` → `Stops
compositor and optionally removes generated units.`
Verify: `sed -n '28,60p' /usr/lib/uwsm/signal-handler.sh` and
`uwsm stop -h`.

## Hypothesis resolution

| Ticket hypothesis | Verdict | Evidence |
| --- | --- | --- |
| **H1** — wlogout action is a forceful user teardown (primary) | **Confirmed as trigger** | `layout:15`; both sessions 2 and 3 removed; `terminate-user` semantics |
| **H2** — the Wayland greeter/weston never restarts | **Refuted as root cause** | No second `Adding new display`/`Display server started`; `Display::stop()` and `Seat::displayStopped()` never ran. weston is only started by `createDisplay()`; it is not failing to restart because nobody asks it to. |
| **H3** — sddm-helper / uwsm / PAM teardown crash (primary) | **Confirmed as failure mode; not a PAM crash** | logind's SIGTERM+SIGHUP kills the helper; exit code 1 → `HELPER_AUTH_ERROR` → no `stop()`. This is an SDDM exit-code-handling defect. |
| **H4** — Pixie login-timeout patch (secondary) | **Refuted** | No greeter is started at all; `interval: 0` is read only by a running greeter. `SessionTimeout=0` also only affects a running greeter. |

## Layer attribution

| Layer | Owner | Attribution |
| --- | --- | --- |
| wlogout Logout action | `dotfiles-assets` | **Immediate trigger.** `loginctl terminate-user $USER` (`configs/wlogout/layout:15`) tears down the helper's session scope. Proposed one-line change: `uwsm stop`. |
| SDDM 0.21.0 helper-exit handling | upstream SDDM (systemic) | **Failure mode.** Exit code 1 (SIGHUP) is cast to `HELPER_AUTH_ERROR`; the greeter restart is skipped. Upstream [#1908](https://github.com/sddm/sddm/issues/1908); PR [#2103](https://github.com/sddm/sddm/pull/2103) is open and not in 0.21.0. |
| SDDM config / weston / Pixie | `dotfiles-provision` | **Not at fault.** The Wayland greeter and weston work on first login; no SDDM config knob changes how a signal-killed helper's exit code is classified. The Pixie timeout patch is inert in this failure. |
| uwsm / session / autostart | `dotfiles-v3` / assets corpus | **Not at fault.** `uwsm` stops cleanly on HUP/TERM; the session entry and `uwsm start` wrapper work. The wrong verb is chosen by wlogout. The v3 pin still needs a bump to deploy the assets fix. Note: as read on 2026-10-26, `dotfiles-v3/dotfiles/` has manifests only — no uwsm/session/autostart file; the session entry is package-provided `/usr/share/wayland-sessions/hyprland-uwsm.desktop` and the Hyprland autostart is assets `configs/hypr/autostart.lua`. |

## Remaining unknown

The code path says the graceful actions should produce a normal helper exit and
a new greeter, and `terminate-session` should still reproduce the bug because
it stops the same session scope. **Neither is proven on this exact stack
without running the VM matrix.** The matrix is required before implementing
the fix; specifically:

- Does `uwsm stop` from the wlogout/AGS environment return to Pixie in <30 s
  with `Auth: sddm-helper exited successfully`?
- Does `hyprctl dispatch exit` behave the same?
- Does `loginctl terminate-session "$XDG_SESSION_ID"` reproduce exit 1/no
  greeter (expected), or does it avoid the SIGHUP race?
- The VM's stock autologin session is `hyprland.desktop` (plain
  `/usr/bin/start-hyprland`), **not** the production
  `hyprland-uwsm.desktop`. The matrix must use the uwsm session; see
  [vm-matrix.md](./vm-matrix.md).
  Evidence: `dotfiles-v3/dev/vm-fresh.sh:346-352` writes
  `Session=hyprland.desktop`; `/usr/share/wayland-sessions/hyprland.desktop:4`
  is `Exec=/usr/bin/start-hyprland`.
  Verify: `sed -n '346,352p' dotfiles-v3/dev/vm-fresh.sh` and
  `grep -n '^Exec=' /usr/share/wayland-sessions/hyprland.desktop`.

## Recommended fix

**Owner: `dotfiles-assets`** (`configs/wlogout/layout`, line 15). Do **not**
edit wlogout until the user approves. The VM matrix must pass case C
(`uwsm stop`) — ideally D as well — before this is implemented; if C/D fail,
the wlogout change is not the fix.

Exact one-line change:

```diff
-    "action" : "loginctl terminate-user $USER",
+    "action" : "uwsm stop",
```

Why `uwsm stop` rather than `loginctl terminate-session`:

- `uwsm stop` stops the compositor unit through the user manager. The
  `uwsm start` wrapper exits normally, the helper exits 0, and SDDM takes the
  `HELPER_SUCCESS` → stop → new greeter path.
- `loginctl terminate-session` still stops the session scope; systemd sends
  SIGTERM+SIGHUP to the helper, so it is expected to produce the same exit 1.
  The matrix confirms; if it unexpectedly returns, it is still a logind-wide
  teardown and less precise than the session manager's own stop.

No provision config change is recommended: no SDDM setting changes how a
signal-killed helper's exit code is classified. A systemic fix would be an
SDDM patch/backport of upstream PR #2103 (restart the greeter when the helper
is signal-killed), but that is out of scope for this ticket and is not needed
to restore the user-facing path.

### Cross-repo release path

The assets corpus is pinned at `v0.6.0`
(`dotfiles-v3/dotfiles/provisioning/assets.yaml:20`). The fix therefore needs:

1. an assets ticket (proposal below) → one-line change, `make
   validate-configs` / `make gates`, new tag (e.g. `v0.6.1`);
2. bump `assets.tag` and the `v0.6.0` source paths in
   `dotfiles-v3/dotfiles/provisioning/assets.yaml`;
3. re-provision the host (or deploy the one file) and run the 5-cycle
   acceptance.

### Proposed assets ticket (not filed; needs approval)

```text
dir:  tickets/bug-001-wlogout-logout-uwsm-stop/
id:   BUG-001
title: "wlogout Logout uses terminate-user and leaves SDDM on a black VT"
kind: bug
status: triage
lane: 2 — bounded config change
severity: high
links:  openspec: none
        bmad: none
worktree: none (create after approval)
branch: none
repro: "In the dotfiles VM, run wlogout -> Logout (key e); the screen stays on a
        black VT and SDDM logs `Auth: sddm-helper ... crashed` / `exited with 1`
        with no second `Greeter starting`."
observed: "Same signature as dotfiles-provision BUG-005: helper dies with exit 1,
           SDDM reports ERROR_INTERNAL \"Process crashed\", no greeter/weston restart,
           power cycle required. 8/8 boots."
expected: "Logout returns to the Pixie greeter on seat0 in <30 s, no helper crash,
           subsequent login works, repeated 5 times."
```

Body:

- **Repro:** `dotfiles-assets/configs/wlogout/layout:15` is
  `loginctl terminate-user $USER`; root cause in `dotfiles-provision` BUG-005
  attribution.
- **Fix:** change line 15 to `"action" : "uwsm stop",`; no other file changes.
- **Why:** `terminate-user` kills the session scope, including the SDDM helper;
  logind's SIGHUP makes it exit 1, which SDDM 0.21 aliases to
  `HELPER_AUTH_ERROR` and skips the greeter restart. `uwsm stop` lets the
  compositor/session manager exit first, so the helper exits 0.
- **Validation:** `make validate-configs`, `make gates`; VM matrix in
  `dotfiles-provision` BUG-005 must show `uwsm stop` returns to the greeter.
- **Release/pin:** new assets tag; bump `assets.tag` + `v0.6.0` paths in
  `dotfiles-v3/dotfiles/provisioning/assets.yaml`; re-provision; host 5-cycle
  acceptance.
- **Cross-link:** `dotfiles-provision` BUG-005.

The user must approve the wlogout behavior change before this ticket is filed
or implemented.

## Acceptance (after the fix is approved and deployed)

- Logout from wlogout returns to the Pixie greeter on seat0 in **< 30 s**.
- No `ERROR_INTERNAL "Process crashed"` / `sddm-helper exited with 1` for the
  user-session helper.
- A subsequent login works; repeat **5 times**, each session up at least 180 s
  (the session checker treats a shorter logout as an early logout).
- `python3 scripts/check-session-bounce.py --since "<start>"` (from
  `dotfiles-v3`) exits 0 with five clean cycles.
- VM regression: the `uwsm stop` case in [vm-matrix.md](./vm-matrix.md) shows
  `Auth: sddm-helper exited successfully` and a second `Greeter starting`.

## References

- SDDM issue #1908 — <https://github.com/sddm/sddm/issues/1908>
- SDDM PR #2103 (open; restart greeter on signal-killed helper) —
  <https://github.com/sddm/sddm/pull/2103>
- SDDM v0.21.0 `src/auth/Auth.cpp`, `src/auth/Auth.h`,
  `src/daemon/Display.cpp`, `src/daemon/Seat.cpp`,
  `src/helper/HelperApp.cpp`, `src/helper/UserSession.cpp` —
  <https://github.com/sddm/sddm/tree/v0.21.0>
- systemd v262 `src/login/logind-dbus.c:4517-4521` (SendSIGHUP) —
  <https://github.com/systemd/systemd/blob/v262/src/login/logind-dbus.c>
- Qt 6.12 `src/3rdparty/forkfd/forkfd.c:252-258`,
  `src/corelib/io/qprocess_unix.cpp:1328-1329` —
  <https://github.com/qt/qtbase/tree/v6.12.0>
- uwsm `signal-handler.sh` and `stop_wm()` —
  `/usr/lib/uwsm/signal-handler.sh`, `/usr/share/uwsm/modules/uwsm/main.py`
