---
id: REQ-057
title: "Provision the Neovim binary: engine package maps + verify"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-057/
branch: ticket/REQ-057-neovim-package-map
---

# Provision the Neovim binary: engine package maps + verify

## Why

The composition requests packages by logical name; the engine's group_vars are
the install authority. Neovim is absent from both, so a provisioned host has no
`nvim` binary even though `~/.config/nvim` is deployed.

This ticket makes the engine able to install Neovim. The composition manifest
entry is tracked separately in `dotfiles-v3` `REQ-118`; the assets config is
`dotfiles-assets` `req-029`.

## Requirement

1. `ansible/inventory/group_vars/arch.yml`: add `neovim: neovim` under
   `packages`.
2. `ansible/inventory/group_vars/debian-family.yml`: add `neovim: neovim`
   under `packages` (both distros use the package name `neovim`).
3. `ansible/roles/verify/vars/main.yml`: add `nvim` to
   `verify_system_binaries`, so a missing binary fails the criterion-2 PATH
   gate instead of silently leaving an unusable editor.
4. Add focused tests:
   - both group_vars maps contain `neovim: neovim`;
   - `verify_system_binaries` contains `nvim`.
5. If the engine's fixture `tests/fixtures/composition/dotfiles/provisioning/packages.yaml`
   is meant to mirror the composition, add the entry there and update the
   hardcoded snapshot at
   `tests/unit/adapters/test_yaml_manifest_reader.py:529-615`. This is a fixture
   consistency edit, not a release.
6. Run the targeted tests plus `make gates` (or the available subset). Do not
   run an apply/provision.

## Forbidden in this ticket

- No git tag, release, or release-note publication.
- No merge to `master`/`main`; leave the work on the ticket branch.
- No release-metadata change: no version bump, no CHANGELOG release heading, no
  engine tag metadata.
- No `installer.pin` bump anywhere.
- No package install, no `ansible-playbook` apply, no `pacman`/`apt`, no
  provisioning run.
- No touching any `ags-*`, `ags-platform`, or other UI worktree/repo.
- Do not edit `dotfiles-v3` manifests or pins here.

## Dependency / sequencing

`dotfiles-v3` `REQ-118` adds the logical `neovim` entry to the composition
manifest. Until this engine change is **released and pinned**, that composition
entry is inert: the `packages` role flattens only mapped group_vars values, so
an unmapped logical key silently does not install. That is acceptable for the
implementation-only phase; the release/pin step is deferred until the user
authorizes shipping.

## Acceptance

- [x] `arch.yml` and `debian-family.yml` both map `neovim: neovim`.
- [x] `verify_system_binaries` contains `nvim`.
- [x] Focused mapping/verify tests pass; any fixture mirror is consistent.
- [x] `make gates` (or the available subset) passes without applying anything.
- [x] No tag, release, `installer.pin` change, package install/apply, or UI
      worktree was touched.

## Evidence

- No Neovim mapping today:
  `ansible/inventory/group_vars/arch.yml`,
  `ansible/inventory/group_vars/debian-family.yml`.
- PATH gate list: `ansible/roles/verify/vars/main.yml:628-669`.
- Package flattening skips unmapped logical keys:
  `ansible/roles/packages/tasks/main.yml` `Assemble package list`.
- Composition copy entry exists:
  `dotfiles-v3/dotfiles/provisioning/config-copies.yaml:33-34`.
- Host check: `command -v nvim` is empty on the current host; the config
  symlink `~/.config/nvim -> ~/.local/share/dotfiles/config/nvim` exists.

## Next step

From `dotfiles-provision`:

```bash
bash scripts/worktree-guard.sh create REQ-057 neovim-package-map
```

Implement on `ticket/REQ-057-neovim-package-map`. Do not tag, release, bump
`installer.pin`, or apply.


## Notes

Originally filed as `REQ-045`; renumbered to `REQ-050` when
`.worktrees/REQ-045/` was found on the unrelated
`ticket/REQ-045-assets-v0200-pin` branch. It was renumbered again to `REQ-057`
when the parallel sound work took `REQ-050` (`.worktrees/REQ-050-r4/`,
`ticket/REQ-050-sound-round4`). Neither existing worktree was touched.

## Release-time note (not now)

At release time the engine `main` was at `v0.1.88` and the composition pinned
assets `v0.21.5`. This branch was rebased onto `main` at `f7f28b4` and the
targeted tests were rerun; pick the next available engine tag at release (do not
reuse an existing tag).

## Release evidence (in progress)

- `dotfiles-assets v0.21.6` released and pushed (LazyVim nvim config).
- Every engine assets mirror, fixture, pin-audit entry and hardcoded assertion
  moved to `v0.21.6`; release metadata is `0.1.89`.
- `make gates-pin` PASS (`assets=v0.21.6, contracts=v0.12.0, platform=v1.2.0`).
- `make assets-parity` PASS (`10 passed, 0 skipped`, assets `v0.21.6`).
- `make build` PASS (`dotfiles_provision-0.1.89` sdist + wheel; wheel carries
  the Ansible tree + group_vars).
- Test shards 1/4, 2/4, 3/4 and 4/4 PASS (shard 3: `377 passed, 2 skipped,
  52 deselected in 2588.26s`). All four hermetic shards PASS (shard 3: `377 passed, 2 skipped, 52 deselected in 2707.62s`).
