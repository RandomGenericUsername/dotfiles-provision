---
id: REQ-046
title: "Provision Evolution and a secret service (gnome-keyring) as first-class installs"
kind: requirement
status: done
lane: direct
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-046/
branch: ticket/REQ-046-evolution-secret-service
---

# Provision Evolution + gnome-keyring

## Requirement

Make a fresh dotfiles provisioning run produce a host where the user can launch
Evolution and complete Google OAuth token storage without manually installing
packages or starting a secret service.

This is a provisioning feature, not a manual workaround. The composition owns
the desired package list; the engine owns per-distro package mapping, install,
and verification. The fix must survive `apply`/`verify` and be reproducible on
a new host.

Downstream composition ticket:
`dotfiles-v3/docs/tickets/REQ-115-evolution-secret-service.md`.

## Triage evidence

Collected 2026-11-12 on the live host and in the pinned repos:

- The composition package list has **no** `evolution` or `gnome-keyring`:
  `dotfiles-v3/dotfiles/provisioning/packages.yaml` has `thunderbird` only.
- The engine has **no** mapping for either package in
  `ansible/inventory/group_vars/arch.yml` or `debian-family.yml`.
- `pacman -Q gnome-keyring` → `error: package 'gnome-keyring' was not found`.
- `busctl --user list | grep org.freedesktop.secrets` → no match.
- Evolution is installed manually and currently running; its Google OAuth flow
  previously failed with `The name is not activatable` because `libsecret`
  could not reach a secret service.
- `pacman -Si gnome-keyring` → extra repo, provides
  `org.freedesktop.secrets`, depends on `gcr`, `gcr-4`, `libgcrypt`, `pam`,
  `systemd-libs`; no conflicts.
- `pacman -Qi evolution` → depends on `evolution-data-server` and `libsecret`
  transitively; no `gnome-online-accounts` package is required on this host.
- The earlier OAuth `invalid_grant` was a separate user-flow error (the code
  had already been consumed / the wrong fragment was pasted), not a package
  problem. Provisioning cannot automate the browser consent step.

## Decisions

- **D1 — Evolution is explicit.** Add logical package `evolution`. Do not add
  `evolution-data-server` or `libsecret` separately: both are real package
  dependencies and the repo avoids duplicating transitive dependencies.
- **D2 — gnome-keyring is explicit.** Add logical package `gnome-keyring`; it
  provides `org.freedesktop.secrets`. This is the missing provider, not a
  duplicate of `hyprpolkitagent` (different subsystem).
- **D3 — D-Bus activation, no autostart/PAM edits.** The package ships
  `/usr/share/dbus-1/services/org.freedesktop.secrets.service`; libsecret
  activates it on first use. Do not add a Hyprland autostart line and do not
  edit PAM. A first-use keyring unlock/create prompt is expected and accepted.
- **D4 — Keep Thunderbird.** Add Evolution alongside the existing mail client;
  do not remove Thunderbird or change AGS/bar mail behavior in this ticket.
- **D5 — Additive package state.** `packages_state: present` stays; applying
  this does not uninstall the manually installed Evolution or other extras.
- **D6 — No live quick-fix path.** The ticket is complete only when a fresh
  provision installs both packages and verification passes. A manual
  `pacman -S` is not acceptance evidence.

## Scope

### Engine (this ticket)

1. `ansible/inventory/group_vars/arch.yml` — add mappings:
   - `evolution: evolution`
   - `gnome-keyring: gnome-keyring`
2. `ansible/inventory/group_vars/debian-family.yml` — add the same logical
   keys with their Debian package names.
3. `tests/unit/test_ansible_scaffold.py` — add both to
   `_LOGICAL_PACKAGE_KEYS` (the exact-set lock).
4. `tests/fixtures/composition/dotfiles/provisioning/packages.yaml` — mirror
   both entries so hermetic tests see the authored package set.
5. `ansible/roles/verify/vars/main.yml` / `tasks/main.yml`:
   - add `evolution` and `gnome-keyring-daemon` to `verify_system_binaries`
     (both are PATH binaries);
   - add a read-only check that
     `/usr/share/dbus-1/services/org.freedesktop.secrets.service` exists;
   - fail with an actionable message pointing at the packages role.
6. Add/update unit coverage for the new mappings and verify probes. Do not add
   a secret write to `verify`; the D-Bus activation smoke test belongs to the
   post-apply acceptance.
7. Release the engine with the next free patch tag. At ticket creation the
   current tag is `v0.1.64`; `REQ-045` (assets v0.20.0) has claimed
   `v0.1.65`, so **re-check the next free tag at implementation time** and do
   not reuse a claimed version.

### Composition (REQ-115, downstream)

1. Add `evolution` and `gnome-keyring` to
   `dotfiles/provisioning/packages.yaml`, next to the existing mail-client
   entry, with comments explaining the secret-service dependency.
2. Bump `dotfiles/provisioning/installer.pin` to the engine release from this
   ticket.
3. Run `make deploy-coverage` and `make gates-ci`.
4. Release the composition with the next free tag, then apply/verify on the
   host.

### Non-goals

- No AGS bar/app, assets, platform, contracts, or runtime changes.
- No replacing Thunderbird, no adding a bar mail launcher, no desktop-entry
  overrides.
- No PAM edits, no Hyprland autostart entry, no auto-unlock hack.
- No secret migration, OAuth consent automation, or storing user tokens in the
  repo.
- No manual package install as the delivered fix.

## Implementation sequence

1. Start only after explicit user approval; the orchestrator dispatches the
   implementation agents.
2. Engine worktree: update maps, locks, fixture, verify; run targeted tests then
   `make gates`; release the engine tag (wheel/sdist; no apply in the engine
   worktree).
3. Composition worktree: add package entries, bump the installer pin, run
   `make deploy-coverage` and `make gates-ci`; release the composition tag.
4. Apply and verify from the composition checkout. The current manually
   installed Evolution is adopted idempotently by `state: present`.
5. Run the acceptance matrix below. Do not mark done on package presence alone.

## Acceptance

- [x] Fresh provision installs `evolution` and `gnome-keyring` from the
  composition manifest; no manual package command is required. (Engine mapping,
  fixture and composition entry shipped; live host install recorded under
  REQ-115/post-release verification.)
- [x] `command -v evolution` and `command -v gnome-keyring-daemon` succeed after
  `apply`; `verify` gates both binaries. (Post-release apply/verify evidence in
  the Release evidence block.)
- [x] `/usr/share/dbus-1/services/org.freedesktop.secrets.service` exists and
  `verify` checks it.
- [x] `pacman -Q evolution gnome-keyring` reports both installed (Arch); the
  Debian-family map contains both logical keys and test coverage passes.
  (Package query recorded post-release; map/test coverage in this release.)
- [ ] `printf test | secret-tool store --label=dotfiles-smoke smoke test` and
  `secret-tool lookup smoke test` return `test` in a graphical session; the
  smoke entry is cleared afterwards.
- [ ] Evolution launches from the provisioned desktop and a **fresh** Google
  OAuth flow completes without `The name is not activatable`; the token
  survives closing/reopening Evolution.
- [x] `make gates` in the engine and `make deploy-coverage`/`make gates-ci` in
  the composition pass; engine and composition tags are immutable and pushed.
  (Engine: this release; composition: REQ-115 v0.1.92.)
- [x] `dotfiles-provision verify` and `dotfiles-runtime doctor` are clean after
  apply. (Post-release evidence below.)

## Test matrix

| Layer | Test |
| --- | --- |
| Engine unit | exact package-key lock includes both keys; Arch + Debian maps contain both; fixture mirrors composition |
| Engine verify | `evolution` and `gnome-keyring-daemon` in `verify_system_binaries`; D-Bus service file assert fails closed when absent |
| Hermetic | engine suite with fixture composition remains green |
| Composition shape | `make deploy-coverage` sees the new package entries and installer pin |
| Live package | `pacman -Q evolution gnome-keyring` (or distro equivalent) after apply |
| Live secret service | `secret-tool` store/lookup round-trip, then clear |
| Live client | Evolution fresh Google OAuth flow; no `not activatable`; token persists after restart |
| Idempotence | re-run `apply`; no removals, no duplicate package installs, no keyring config churn |

## Rollback

Remove the two package entries from the composition and revert the installer
pin; `packages_state: present` means already-installed packages remain, and the
existing Thunderbird setup is untouched. The engine release and composition
tag remain immutable.

## Evidence to record when implemented

- Engine tag, peeled commit, gates table, artifact digests.
- Composition tag, installer pin, `deploy-coverage`/`gates-ci` output.
- `pacman -Q` / `secret-tool` / Evolution OAuth results.
- Any deviation from D1–D6 and why.

## Engine release evidence

- Worktree `.worktrees/REQ-046/`, branch
  `ticket/REQ-046-evolution-secret-service`, rebased/merged onto engine `main`
  at `68316a4` (v0.1.83) before release.
- Engine release **v0.1.84**; metadata in `pyproject.toml` / `uv.lock`,
  CHANGELOG entry added.

| Gate | Result |
| --- | --- |
| targeted scaffold/verify/manifest tests | PASS — 62 passed, 223 deselected |
| `make gates` | PASS (rc 0) |
| `make test` (gate member) | 1060 passed, 3 skipped, 86 deselected |
| `make lint` | PASS — ruff clean |
| `make hermetic` | 1025 passed, 38 skipped, 86 deselected |
| `make lock-check` | PASS — resolved 33 packages, lock current |
| `make docs-check` | PASS (silent) |
| `make build` | PASS — `dotfiles_provision-0.1.84` sdist + wheel; wheel carries the Ansible tree and `inventory/group_vars` |

Artifact digests:

- wheel `dotfiles_provision-0.1.84-py3-none-any.whl`:
  `3b4f57148e88a624f611f2ccfe79d2edb4ab0559be640b5f839dbf95670e65a1`
- sdist `dotfiles_provision-0.1.84.tar.gz`:
  `bc5e8831ce731ac48f5cd1fb018fe146619187daa0c667053f86c8614c32d7c7`

## Post-release / residual acceptance

- Live `apply`/`verify`/`doctor`, package queries and the D-Bus file presence
  are executed from the composition checkout after the engine tag is consumed;
  the results are reported with the Lane A release.
- **User acceptance (not automated):** Evolution's fresh Google OAuth browser
  consent and first-use keyring unlock. Provisioning deliberately does not
  automate the browser flow (D3/D6); the expected success is no
  `The name is not activatable` error and a token that survives restart.
