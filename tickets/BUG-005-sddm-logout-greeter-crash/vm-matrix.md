# BUG-005 VM-only logout matrix

**Purpose:** prove which logout verb lets SDDM restart the Pixie greeter, and
which reproduces the helper exit-1 black screen.
**Run only in the disposable Incus VM.** Never run these commands on the host;
the host logout is currently destructive (black VT + power cycle). `sudo` and
the VM are user-run steps.
**Status:** prepared, not run. Paste the results back into BUG-005 before the
fix is implemented.

The matrix follows the attribution in
[attribution.md](./attribution.md). The expected result is:

- `loginctl terminate-user` (wlogout) → **reproduces** the bug;
- `loginctl terminate-session` → likely reproduces (same session-scope
  SIGTERM+SIGHUP), to be proven;
- `uwsm stop` → **greeter returns** (proposed fix);
- `hyprctl dispatch exit` → **greeter returns** (control for the compositor's
  own exit path).

## 0. Prepare a fresh VM with the production uwsm session

From the `dotfiles-v3` checkout on the host:

```sh
cd ~/Development/dotfiles-v3
make vm-fresh          # sudo: wipe/recreate, provision, reboot, assert
make vm-up             # only if the VM is stopped
```

The stock `vm-fresh` autologin drop-in uses `Session=hyprland.desktop`, which
is **plain Hyprland** (`Exec=/usr/bin/start-hyprland`), not the production
`hyprland-uwsm.desktop` (`Exec=uwsm start -e -D Hyprland hyprland.desktop`).
Switch it before testing:

```sh
sudo incus exec dotfiles-test -- bash -c 'cat > /etc/sddm.conf.d/90-dotfiles-vm-autologin.conf <<"EOF"
[Autologin]
User=arch
Session=hyprland-uwsm.desktop
EOF
systemctl restart sddm'
```

Wait for the session, then verify the production shape:

```sh
sudo incus exec dotfiles-test -- bash -c '
for i in $(seq 1 30); do
  sid=""
  for s in $(loginctl show-user arch -p Sessions --value); do
    [ "$(loginctl show-session "$s" -p Seat --value)" = seat0 ] && sid="$s"
  done
  [ -n "$sid" ] && break
  sleep 1
done
echo "SID=$sid"
loginctl show-session "$sid" -p Id -p Type -p Class -p Desktop -p Scope -p Leader
ps -o pid,ppid,user,args -p "$(loginctl show-session "$sid" -p Leader --value)"
'
```

Required: `Desktop=Hyprland`, `Class=user`, `Type=wayland`, and the leader
command line contains
`--start uwsm start -e -D Hyprland hyprland.desktop --user arch`.

If the uwsm autologin does not come up, disable autologin and log in through
the Pixie greeter instead (choose **Hyprland (uwsm-managed)** in the session
menu):

```sh
sudo incus exec dotfiles-test -- rm -f /etc/sddm.conf.d/90-dotfiles-vm-autologin.conf
sudo incus exec dotfiles-test -- systemctl restart sddm
make vm-console        # SPICE window; Ctrl+Alt+G to grab the keyboard
```

Open the graphical console (`make vm-console`), press **Ctrl+Alt+G**, then
**Super+Enter** to open kitty. Confirm the terminal is in the graphical
session:

```sh
echo "USER=$USER XDG_SESSION_ID=$XDG_SESSION_ID XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"
```

Expected: `USER=arch`, a non-empty session ID (usually `2`), and
`XDG_RUNTIME_DIR=/run/user/1000`.

## 1. Capture harness (host shell)

Run these from the host, in one shell. `CASE` is changed per case.

```sh
VM=dotfiles-test
OUT="$HOME/bug-005-vm"
mkdir -p "$OUT"
```

Preflight — prove the VM has the same scope/SIGHUP/helper shape as the host:

```sh
CASE=A-force-user
mkdir -p "$OUT/$CASE"
sudo incus exec "$VM" -- bash -c '
sid=""
for s in $(loginctl show-user arch -p Sessions --value); do
  [ "$(loginctl show-session "$s" -p Seat --value)" = seat0 ] && sid="$s"
done
echo "SID=$sid"
systemctl show "session-$sid.scope" -p KillMode -p KillSignal -p SendSIGHUP
h=$(pgrep -f "sddm-helper.*--start.*--user arch" | head -1)
echo "HELPER=$h"
grep -E "SigCgt|SigIgn" "/proc/$h/status"
' | tee "$OUT/$CASE/preflight.txt"
```

Expected: `KillSignal=15`, `SendSIGHUP=yes`, `KillMode=control-group`;
`SigCgt` includes 2, 15 and 17 but not 1 (SIGHUP). This is the same mechanism
as the host capture.

Per-case capture — start a timestamp, run the action in kitty, then wait 30 s
and collect:

```sh
CASE=A-force-user          # change per case
mkdir -p "$OUT/$CASE"
T0=$(sudo incus exec "$VM" -- date +%s)
sudo incus exec "$VM" -- logger -t bug005 "CASE=$CASE START"

# ... run the one-line action in the VM's kitty here ...

sleep 30
sudo incus exec "$VM" -- journalctl -b --since "@$T0" --no-pager -o short-precise \
  > "$OUT/$CASE/journal.log"
sudo incus exec "$VM" -- journalctl -b -u sddm --since "@$T0" --no-pager -o short-precise \
  > "$OUT/$CASE/sddm.log"
sudo incus exec "$VM" -- bash -c '
echo "== sessions =="; loginctl list-sessions --no-pager
echo "== weston =="; pgrep -a weston || true
echo "== greeter =="; pgrep -a sddm-greeter || true
echo "== sddm =="; systemctl is-active sddm
' > "$OUT/$CASE/state.txt"
sudo incus exec "$VM" -- logger -t bug005 "CASE=$CASE END"

grep -nE 'Adding new display|Removing display|Display server started|Greeter starting|Greeter stopped|Session started|sddm-helper|Process crashed|exited with' \
  "$OUT/$CASE/sddm.log"
```

Also record the journal's session/scope lines for each case:

```sh
grep -nE 'session-[0-9]+\.scope|Stopping Session|Removed session|SIGHUP|SIGTERM|sddm-helper' \
  "$OUT/$CASE/journal.log"
```

## 2. Cases (run in the VM's kitty)

Run each case from a fresh login after the previous case. The first case
reproduces the wlogout action; the last two test the proposed graceful paths.

| # | Case | Exact command in the VM session | Expected |
| --- | --- | --- | --- |
| A | Force user (wlogout equivalent) | `loginctl terminate-user "$USER"` | **Black VT; no greeter.** `crashed (exit code 1)` / `exited with 1`; sessions 2 and 3 removed; no weston/greeter; `sddm` active. |
| B | Graceful session | `loginctl terminate-session "$XDG_SESSION_ID"` | To be recorded. Expected: same helper exit 1/no greeter (the scope still gets SIGTERM+SIGHUP); session 3 remains. |
| C | uwsm stop | `uwsm stop` | **Pixie greeter returns <30 s.** `Auth: sddm-helper exited successfully`; second `Greeter starting...` / `Display server started.`; weston + greeter processes present. |
| D | Compositor exit | `hyprctl dispatch exit` | **Pixie greeter returns <30 s.** Same clean helper exit/second greeter as C. |

### Case A — force user (wlogout equivalent)

In kitty:

```sh
loginctl terminate-user "$USER"
```

The terminal and the whole session disappear. Wait 30 s. If the greeter does
not return, run the capture block above from the host. Then recover:

```sh
sudo incus exec dotfiles-test -- systemctl restart sddm
```

If the VT is still dead after 10 s, `sudo incus restart dotfiles-test` and wait
for the session; record that recovery was needed.

### Case B — graceful session

After logging in again, in kitty:

```sh
loginctl terminate-session "$XDG_SESSION_ID"
```

Capture. Recover as in A if needed. If the greeter returns, note the time and
log in again.

### Case C — uwsm stop

After logging in again, in kitty:

```sh
uwsm stop
```

Capture after 30 s. If the Pixie greeter is visible, note the time from command
to greeter. Log in again for case D.

### Case D — compositor exit

After logging in again, in kitty:

```sh
hyprctl dispatch exit
```

Capture after 30 s. The greeter should return. This is the control for the
compositor's own shutdown path.

## 3. Results table (paste back)

| Case | Greeter returned? | Time to greeter | Helper exit line | Session 2 removed? | Session 3 removed? | Weston/greeter after? | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A force-user | | | | | | | |
| B terminate-session | | | | | | | |
| C uwsm stop | | | | | | | |
| D hyprctl exit | | | | | | | |

For each case, paste:

- `preflight.txt` (once, case A);
- the `grep` output from `sddm.log`;
- `state.txt`;
- the session/scope `grep` from `journal.log`;
- one line: "Pixie greeter visible? yes/no; if yes, N seconds."

To keep the output small, `sddm.log` and `journal.log` themselves can stay on
the host; paste the greps and the state.

## 4. How the results decide the fix

- **C and D return, A and B fail** → the fix is the wlogout action; use
  `uwsm stop` (preferred) and file the assets ticket proposed in
  `attribution.md`.
- **C returns but D does not** → still use `uwsm stop`; the compositor's exit
  dispatch is not reliable on this stack.
- **B returns but A fails** → `terminate-session` would avoid the failure, but
  it is still a logind-wide teardown; `uwsm stop` remains the cleaner fix.
- **A, B, C and D all fail** → the wlogout action is not the only problem; stop
  and escalate to the SDDM helper-exit handling (upstream PR #2103 / a
  backport), and do not implement the wlogout change yet.

## 5. Recovery between cases

- If the greeter returns: log in through Pixie as `arch` / `arch`, wait for the
  Hyprland session, and run the next case.
- If the screen is a black VT: from the host,
  `sudo incus exec dotfiles-test -- systemctl restart sddm`. The VM autologin
  (if still enabled) starts a fresh session. If SDDM cannot recover the VT,
  `sudo incus restart dotfiles-test`; record it.
- Do not power-cycle or log out the host.

## 6. After the fix: host 5-cycle acceptance (user-run)

Only after the assets change is approved, tagged, pinned in
`dotfiles-v3/dotfiles/provisioning/assets.yaml`, and re-provisioned:

1. Log in through the Pixie greeter, keep the session up at least 180 s, then
   wlogout → Logout. Time the return to the greeter.
2. Log in again and repeat **5 times**.
3. Capture:

```sh
START='<timestamp before the first logout>'
journalctl -b -u sddm --since "$START" --no-pager \
  | grep -nE 'Greeter starting|Greeter stopped|Session started|Process crashed|sddm-helper exited'
python3 scripts/check-session-bounce.py --since "$START"   # from dotfiles-v3
```

Pass: five cycles, each greeter return <30 s, no `Process crashed` /
`exited with 1` for the user-session helper, a subsequent login works after
each cycle, and the checker exits 0.
