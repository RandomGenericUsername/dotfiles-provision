---
id: REQ-019
title: "Bump ags-platform pin to v0.5.0 (capture-cluster contract)"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-019/
branch: ticket/REQ-019-ags-platform-v050
---

# Bump ags-platform pin to v0.5.0

## Requirement

`ags-platform v0.5.0` adds the `capture-cluster` request contract used by
`ags-bar v0.3.0` and `ags-capture-tool v0.3.x`. The platform tag is mirrored in
the `ags_platform` role, the `verify` role and the composition fixture. Move all
platform mirrors to `v0.5.0`; leave `contracts` and `dotfiles-assets` unchanged.

## Acceptance

- [x] `ansible/roles/ags_platform/vars/main.yml`: `ags_platform_version` is
      `v0.5.0`.
- [x] `ansible/roles/verify/vars/main.yml`: `verify_ags_platform_version` is
      `v0.5.0`.
- [x] Composition fixture `program-tuple.yaml`: `ags-platform: v0.5.0`;
      `contracts` and `dotfiles-assets` unchanged.
- [x] Platform unit-test expectations move to `v0.5.0`.
- [x] `make gates` passes; version `0.1.33` and CHANGELOG entry.
- [x] Annotated tag `v0.1.33` created and pushed after merge; composition
      `installer.pin` can point at it.

## Evidence / Verify

- `rg -n 'v0\.4\.0' ansible/roles/ags_platform ansible/roles/verify tests/fixtures/composition/dotfiles/provisioning/program-tuple.yaml pyproject.toml` → no output.
- `make gates` → exit 0: 945 tests passed, lint passed, 914 hermetic passed, lock-check passed, docs-check passed.
- Tag: `v0.1.33` annotated and pushed after the main merge; composition `installer.pin` points at it.

## Outcome

Released engine `v0.1.33`; composition `dotfiles-v3` PIN-0140 consumes the
`ags-platform v0.5.0` tuple and the `ags-bar v0.3.0` / `ags-capture-tool v0.3.1`
app tags.
