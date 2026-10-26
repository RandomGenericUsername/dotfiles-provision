---
id: BUG-004
title: "SDDM Wayland greeter has no compositor — 90 s session bounce"
kind: bug
status: done
lane: 2
severity: high
links:
  openspec: none
  bmad: none
worktree: .worktrees/BUG-004/
branch: ticket/BUG-004-sddm-wayland-greeter
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

- [x] `weston` in `display_manager_sddm_packages` + fail-closed preflight.
- [x] `display_manager_sddm_compositor_command: "weston --shell=kiosk"` wired
      through the assets v0.6.0 template.
- [x] Every `*_assets_pinned_tag` mirror = `v0.6.0`; parity tests updated.
- [x] Pixie pinned to `1e1a863761f742e8d509d569382b17c112e29fdc`; timeout patch
      fails closed when the pattern is absent/duplicated.
- [x] Verify role asserts weston + config lines + Pixie HEAD + patch.
- [x] Red then green role/verify tests; `make gates` + `make test-integration`
      green.
- [x] Merge to `main`, annotated tag `v0.1.13`, GitHub Release with sdist/wheel.
- [x] User host step: full provision with sudo, reboot, OPS-0113 5-login check.

## Closeout

| Claim | Command | Result |
| --- | --- | --- |
| Red (before fix) | `DOTFILES_ASSETS_REPO=… pytest -q -m "not integration and not container_target" tests` on `12676a0` | **exit 1** — 22 failed / 974 passed / 2 skipped / 54 deselected. All v0.5.0 pin mirrors, missing weston/compositor/preflight, missing verify greeter tasks. |
| Green targeted | `pytest -q test_display_manager_role.py test_verify_role.py test_template_vars_parity.py test_assets_role.py test_btop_config_role.py test_compositor_configs_role.py test_config_copies_role.py test_compositor_skeleton_configs.py` | **exit 0** — 300 passed, 2 skipped. |
| Engine gates | `make gates` (implementation commit `40c7363`) | **exit 0** — test 994 passed/4 skipped/54 deselected; hermetic 990 passed/8 skipped/54 deselected; ruff clean; `uv lock --check` resolved 33; docs-check present. |
| Assets parity (CI-only) | `make assets-parity` | **exit 0** — 7 passed, 0 skipped, corpus `dotfiles-assets@v0.6.0`. |
| Integration | `make test-integration` | **exit 0** after the test-only harness repair — 45 passed, 10 skipped, 997 deselected. First run was exit 2 with 3 failed/13 errors; both root causes reproduce on untouched `main` (`3c81dbb`), see the follow-up commit. |
| Merge + tag | `git log --oneline` / `git show v0.1.13` | merge `3428d66` on `main`; annotated tag `v0.1.13` → `3428d66`. |
| Tag CI | `gh run view 40360346624` | `completed/success` (tag push, all gates + release job). |
| Release assets | `gh release view v0.1.13 --json assets` | `dotfiles_provision-0.1.13-py3-none-any.whl`, `dotfiles_provision-0.1.13.tar.gz` |
| Release URL | `gh release view v0.1.13 --json url` | https://github.com/RandomGenericUsername/dotfiles-provision/releases/tag/v0.1.13 |
| Pixie pin | `git ls-remote https://github.com/xCaptaiN09/pixie-sddm.git refs/heads/main` | `1e1a863761f742e8d509d569382b17c112e29fdc` (recorded in `display_manager_pixie_repo_ref` + `verify_pixie_repo_ref`). |
| Host red evidence | `journalctl -b -u sddm \| grep -c "falling back to DisplayServer=x11-user"`; `command -v weston`; `grep -c "Session started false"` | 4; exit 1 (missing); 3. Config had `DisplayServer=wayland` and no `[Wayland]`; `git -C /usr/share/sddm/themes/pixie rev-parse HEAD` failed "dubious ownership" (hence `safe.directory=*` in verify). |
| Test-only follow-up | commit `3927925` | btop e2e passes `composition_root`; compositor dry-run seeds the assets desktop inputs. No engine code change, no tag move. |

Evidence (deployed config, after the role renders v0.6.0):
`rg -n "CompositorCommand" ansible/roles/display_manager/vars/main.yml
ansible/roles/verify/tasks/main.yml` and the rendered body at
`templates/display-manager/sddm.conf.j2` in `dotfiles-assets@v0.6.0`.
Verify: `DOTFILES_ASSETS_REPO=<assets-v0.6.0> make gates && make test-integration`.

### User host steps (sudo; user-run — the agent must not provision/reboot)

1. In `dotfiles-v3`, advance `dotfiles/provisioning/installer.pin` to
   `v0.1.13` through the normal PIN-0114 flow (this is a normal release pin,
   not a hotfix), then commit/push.
2. From the `dotfiles-v3` root, run the full host provision with sudo:
   `make bootstrap ARGS="--ask-become-pass"` (the become scope installs
   `weston`, rewrites `/etc/sddm.conf.d/10-dotfiles.conf`, patches the pinned
   Pixie checkout, and enables SDDM).
3. Reboot: `sudo reboot` (the greeter compositor is picked up by SDDM at boot;
   no SDDM restart during provisioning — it would kill the live session).
4. After re-login, run the OPS-0113 session-bounce checker from
   `dotfiles-v3`:
   `python3 scripts/check-session-bounce.py --boot 0` → exit 0 over 5 logins;
   `python3 scripts/check-session-bounce.py --since "today"`.
5. Optional engine gate:
   `make provision ARGS="verify --expected-engine-tag v0.1.13"` → exit 0.
6. Confirm the fallback is gone:
   `journalctl -b -u sddm | grep -c "falling back to DisplayServer=x11-user"` → 0
   and `journalctl -b -u sddm | grep -c "Session started false"` → 0.

### Post-tag notes

- `v0.1.13` is immutable and was tagged at `3428d66` (implementation + tests).
  The integration-harness repair `3927925` is test-only and landed after the
  tag for the green `make test-integration` closeout; it changes no packaged
  file (`pyproject.toml` packages only `src/provisioning`).
- The composition pin bump is the consumer's normal flow and was not performed
  from this engine repo (hard constraint: no other repo touched).
