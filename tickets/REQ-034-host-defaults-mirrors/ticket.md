---
id: REQ-034
title: "Mirror contracts v0.9.0 and assets v0.15.0 for the host-defaults cutover"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-034/
branch: ticket/REQ-034-host-defaults-mirrors
---

# Mirror contracts v0.9.0 and assets v0.15.0 for the host-defaults cutover

## Requirement

The composition `SKIN-HOST-DEFAULTS` slice pins `contracts v0.9.0`,
`dotfiles-assets v0.15.0` and `dotfiles-runtime v1.1.0`. Its
`deploy-coverage` cutover fails because the engine mirrors are stale:

```text
FAIL: ansible/roles/assets/vars/main.yml: assets_pinned_tag 'v0.14.0'
must mirror 'v0.15.0'
```

The engine at v0.1.50 also pins `contracts v0.8.0` and vendors the
v0.8.0 generation contract fixtures. Every assets mirror, the composition
fixture, the vendored contract schema/PIN and the hardcoded pin assertions
must move together, so the composition can consume installer v0.1.51 with
contracts v0.9.0 / assets v0.15.0 / runtime v1.1.0.

`contracts v0.9.0` is additive: it adds an **optional** generation-manifest
`host` block (`source: hyprland`, mapping `version: 1`, `fingerprint`,
non-empty `defaults`) and optional `intent.host`, which must equal
`host.fingerprint` when present and must be absent when the block is absent.
Existing host-free v3 manifests remain valid. Verify keeps
`generation_manifest_version: 3` and its hash/current/locality checks, and
must accept a host-bearing manifest as valid runtime output.

Criteria: the composition's `SKIN-HOST-DEFAULTS` cutover; no upstream pin
edits and no runtime changes.

## Acceptance

- [ ] Every engine assets pin/mirror moves from `v0.14.0` to **`v0.15.0`**:
      `assets`, `verify`, `config_copies`, `wlogout_config`, `kitty_config`,
      `btop_config`, `display_manager`, `compositor_configs`, `zsh_config`,
      the composition fixture (`assets.yaml` tag + four checkout sources,
      `program-tuple.yaml`) and hardcoded test assertions.
- [ ] Contracts pins/fixtures move from `v0.8.0` to **`v0.9.0`**:
      `verify_generation_contract_tag`, the vendored
      `tests/fixtures/contracts/v0.9.0/` generation-manifest +
      appearance-refresh-result schemas and PIN/hashes, the fixture
      `program-tuple.yaml`, and hardcoded assertions.
- [ ] Verify keeps `version: 3` and accepts an optional host-bearing manifest;
      a fixture with `host` + `intent.host` passes and a malformed host
      (mismatched fingerprint or host-without-intent) fails. No hash, current
      or locality check is weakened.
- [ ] The v3 app tags, runtime-independent behavior, `state_links` and the
      wlogout appearance link from v0.1.50 are unchanged.
- [ ] No stale `v0.14.0` / `v0.8.0` reference remains outside historical
      tickets and CHANGELOG.
- [ ] Targeted assets/verify/locality/contracts tests, `make gates` and
      `make ci-gates-parity` pass on the ticket branch.
- [ ] Engine `0.1.51` + CHANGELOG, annotated tag `v0.1.51` after the
      fast-forward merge; push `main` and the tag; the GitHub Release carries
      only the 0.1.51 sdist and wheel; no apply.

## Non-goals

- No composition, runtime, app, contract-schema or live-host edit.
- No `apply`, no runtime seed, no downstream consumer edit.
- No change to app tags, state-link targets or wlogout consumer behavior.

## Evidence / Verify

Worktree `.worktrees/REQ-034/`, branch
`ticket/REQ-034-host-defaults-mirrors`. Commits: plan (this file + INDEX),
implementation/release metadata, then evidence. Annotated tag `v0.1.51` on
the fast-forward merge commit; no apply.

Evidence is recorded in this ticket after the gates complete.
