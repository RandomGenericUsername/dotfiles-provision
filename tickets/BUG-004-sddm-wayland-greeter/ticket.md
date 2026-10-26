---
id: BUG-004
title: "SDDM Wayland greeter has no compositor — 90 s session bounce"
kind: bug
status: triage
lane: 2
severity: high
links:
  openspec: none
  bmad: none
worktree: none
branch: none
repro: 'journalctl -b -u sddm | grep -c "falling back to DisplayServer=x11-user"'
observed: "4 × this boot: 'Failed to launch the display server, falling back to DisplayServer=x11-user'; 'command -v weston' exits 1; 3 × 'Session started false' after the x11-user fallback"
expected: "0 fallbacks; weston present; /etc/sddm.conf.d/10-dotfiles.conf carries DisplayServer=wayland + [Wayland] CompositorCommand=weston --shell=kiosk; no 'Session started false'"
---

# BUG-004 — SDDM Wayland greeter has no compositor → 90 s session bounce

## Repro

`journalctl -b -u sddm | grep -c "falling back to DisplayServer=x11-user"`

Supporting probes (no sudo):

```sh
command -v weston                          # exit 1 (missing)
journalctl -b -u sddm | grep -c "Session started false"
cat /etc/sddm.conf.d/10-dotfiles.conf      # DisplayServer=wayland, no [Wayland]
```

## Observed

On this boot (2026-10-26 08:28–08:35, `journalctl -b -u sddm`):

- `Failed to launch the display server, falling back to DisplayServer=x11-user`
  occurs **4×** (`grep -c … = 4`).
- `command -v weston` → exit **1**; none of
  `kwin_wayland weston cage sway wayfire labwc` is installed.
- `/etc/sddm.conf.d/10-dotfiles.conf` renders `DisplayServer=wayland` and
  `GreeterEnvironment=QT_QPA_PLATFORM=wayland` but has **no `[Wayland]` section**
  (assets v0.5.0 template predates req-006).
- After the fallback to `x11-user`, `Session started false` occurs **3×**
  (08:29:59, 08:31:35, 08:33:55), followed by the ~90 s session teardown.
- The same fallback pattern appears in boot -1 (06:23–06:42, 6×), boot 0
  (08:29–08:34, 3×) and 2026-10-17 21:29–21:32 (2×).

Evidence: `journalctl -b -u sddm --no-pager` lines quoted above;
`cat /etc/sddm.conf.d/10-dotfiles.conf`; `command -v weston` exit 1.
Verify: `journalctl -b -u sddm | grep -c "falling back to DisplayServer=x11-user"`.

## Expected

- `weston` is installed (the compositor SDDM's Wayland greeter needs).
- The rendered config keeps `DisplayServer=wayland` and names
  `[Wayland] CompositorCommand=weston --shell=kiosk`.
- The role fails closed if the compositor is absent — no silent `x11-user`
  fallback.
- After the host provision + reboot: `grep -c "falling back…"` = 0 and no
  `Session started false` across 5 logins (OPS-0113 checker).

## Fix notes

Root cause: SDDM is configured for a Wayland greeter but the compositor that
runs it was never installed. SDDM's implicit `Wayland.CompositorCommand` is
`weston --shell=kiosk` ([sddm.conf(5)]), and with no compositor the greeter
display server cannot start; SDDM falls back to `x11-user`, gives the login a
new VT, and `UserSession::start()`/`waitForStarted()` ends in
`Session started false` with the session torn down ~60 s later.

Fix:

1. `weston` in `display_manager_sddm_packages` and a fail-closed preflight
   `command -v weston` assert after the package task.
2. Consume the assets v0.6.0 `sddm.conf.j2` (req-006), which renders
   `[Wayland] CompositorCommand={{ display_manager_sddm_compositor_command |
   default('weston --shell=kiosk') }}`; bump **every** `*_assets_pinned_tag`
   mirror to v0.6.0.
3. Pin the Pixie theme to the tested commit
   `1e1a863761f742e8d509d569382b17c112e29fdc` (`xCaptaiN09/pixie-sddm` `main`
   at 2026-10-26) and make the `interval: 5000` login-timeout patch fail closed
   when the pattern is absent or duplicated.
4. `verify` asserts `weston`, `DisplayServer=wayland`, `[Wayland]` +
   the compositor command, the Pixie HEAD == pin, and the applied timeout
   patch. It does **not** restart SDDM (that would kill the live session).
5. Tests + CHANGELOG; `make gates`, `make test-integration`; release v0.1.13.

Triage: kind `bug` (repro/observed/expected present); lane `2` (bounded single
role + assets pin + tests/verify); severity `high` (recurring login loss, no
data loss). Evidence for the lane: this ticket's Fix section touches one role,
one assets tag bump, the verify mirror and tests; the template/schema capability
ships in `dotfiles-assets` v0.6.0 req-006, so no engine OpenSpec delta.
Verify: `rg -n "^lane: 2|^severity: high" tickets/BUG-004-sddm-wayland-greeter/ticket.md`.

## Done-when

- [ ] `weston` in `display_manager_sddm_packages` + fail-closed preflight.
- [ ] `display_manager_sddm_compositor_command: "weston --shell=kiosk"` wired
      through the assets v0.6.0 template.
- [ ] Every `*_assets_pinned_tag` mirror = `v0.6.0`; parity tests updated.
- [ ] Pixie pinned to `1e1a863761f742e8d509d569382b17c112e29fdc`; timeout patch
      fails closed when the pattern is absent/duplicated.
- [ ] Verify role asserts weston + config lines + Pixie HEAD + patch.
- [ ] Red then green role/verify tests; `make gates` + `make test-integration`
      green.
- [ ] Merge to `main`, annotated tag `v0.1.13`, GitHub Release with sdist/wheel.
- [ ] User host step: full provision with sudo, reboot, OPS-0113 5-login check.
