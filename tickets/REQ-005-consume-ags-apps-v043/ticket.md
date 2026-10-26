---
id: REQ-005
title: "Consume ags-apps v0.4.3 (selector collapses on Apply) + release v0.1.14"
kind: requirement
status: in-progress
lane: 1
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-005/
branch: ticket/REQ-005-consume-ags-apps-v043
---

# REQ-005 — Consume ags-apps v0.4.3 (selector collapses on Apply) + release v0.1.14

## Requirement

The engine SHALL install ags-apps `v0.4.3` (upstream BUG-002: the wallpaper
selector's drawer collapses immediately on Apply) and SHALL assert the same tag
in `verify`. Concretely: `ags_apps_version` and its hand-maintained mirror
`verify_ags_apps_version` both move from `v0.4.2` to `v0.4.3`; the parity test
fails at `v0.4.2` and passes at `v0.4.3`; the CHANGELOG records the bump; the
engine is released as annotated tag `v0.1.14` with a GitHub Release carrying the
sdist and wheel. No other pin (runtime, assets) moves.

## Pin / source evidence

- Upstream tag exists and resolves to the expected commit:

  ```text
  $ git ls-remote --tags https://github.com/RandomGenericUsername/ags-apps 'refs/tags/v0.4.3*'
  ae5d4d6d2df6550b0dd71dad47219518b0daf8ed	refs/tags/v0.4.3
  0503fdb7114e34a5be24171b47a3bd0d5e56da35	refs/tags/v0.4.3^{}
  ```

  The peeled commit `0503fdb` is the expected target (annotated tag object
  `ae5d4d6`). Evidence: command output above.
  Verify: `git ls-remote --tags https://github.com/RandomGenericUsername/ags-apps 'refs/tags/v0.4.3*'`.

- Upstream release metadata:

  ```text
  $ gh release view v0.4.3 --repo RandomGenericUsername/ags-apps \
      --json tagName,name,publishedAt,url
  {"name":"v0.4.3 — BUG-002: selector collapses on Apply click",
   "publishedAt":"2026-10-26T15:25:25Z","tagName":"v0.4.3",
   "url":"https://github.com/RandomGenericUsername/ags-apps/releases/tag/v0.4.3"}
  ```

  Evidence: quoted `gh` output; URL above.
  Verify: `gh release view v0.4.3 --repo RandomGenericUsername/ags-apps --json tagName,name,url`.

- Current engine pins (both `v0.4.2`):
  `ansible/roles/ags_apps/vars/main.yml:102` (`ags_apps_version`) and
  `ansible/roles/verify/vars/main.yml:709` (`verify_ags_apps_version`).
  The parity test is
  `tests/unit/test_verify_role.py::TestVerifyAgsAppsPinMirror`.
  Evidence: `rg -n "ags_apps_version: v0.4.2|verify_ags_apps_version: v0.4.2" ansible/roles`.
  Verify: same command.

- Release-train scope: `.opencode/plan/09-release-train.md:50-53` (section 3.2)
  names `REQ-005-consume-ags-apps-v043 → v0.1.14`, precondition ags-apps
  v0.4.3, change `ags_apps_version` + `verify_ags_apps_version`, `make gates`,
  tag + release.
  Evidence: file path + line range above.
  Verify: `sed -n '50,53p' .opencode/plan/09-release-train.md`.

## Triage

Per `.opencode/commands/triage.md`:

- `kind: requirement` — the request is "consume upstream release v0.4.3 in the
  engine", a bounded behavior/pin requirement (not a bug in this repo, not an
  epic, no parent).
- `lane: 1` — XS direct. Fully understood, two literal pin values plus the
  existing parity test, CHANGELOG, and the standard release procedure. The
  selector fix itself ships in ags-apps; this repo has no OpenSpec capability
  delta (`links.openspec: none`).
- No ambiguity to resolve; BMAD is not invoked.

Evidence: this ticket's pin/source section + `rg -n "ags_apps_version|verify_ags_apps_version" ansible/roles`.
Verify: `rg -n "^kind: requirement|^lane: 1" tickets/REQ-005-consume-ags-apps-v043/ticket.md`.

## Acceptance

- [ ] A red version-mirror/parity test fails at `v0.4.2` and passes at
      `v0.4.3`.
- [ ] `ags_apps_version: v0.4.3` and `verify_ags_apps_version: v0.4.3`.
- [ ] Engine version `0.1.14` (`pyproject.toml`, `src/provisioning/__init__.py`,
      `uv.lock`) and a CHANGELOG entry.
- [ ] `make gates` green in the worktree.
- [ ] Merged to `main`; annotated tag `v0.1.14`; GitHub Release carries the
      sdist and wheel; branch/tag pushed.
- [ ] Runtime (`v0.1.0`), assets (`v0.6.0`), ITR/weg/csg and ags-platform
      (`v0.2.0`) pins unchanged.

## Out of scope

- ags-apps internals: the selector fix ships upstream in v0.4.3.
- Runtime v0.2.0 mirror (`REQ-006`, separate ticket/agent).
- Host deployment/provisioning (user-run, later via `dotfiles-v3` PIN-0114).
