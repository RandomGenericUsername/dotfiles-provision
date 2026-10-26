---
id: REQ-005
title: "Consume ags-apps v0.4.3 (selector collapses on Apply) + release v0.1.14"
kind: requirement
status: done
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

- [x] A red version-mirror/parity test fails at `v0.4.2` and passes at
      `v0.4.3`.
- [x] `ags_apps_version: v0.4.3` and `verify_ags_apps_version: v0.4.3`.
- [x] Engine version `0.1.14` (`pyproject.toml`, `src/provisioning/__init__.py`,
      `uv.lock`) and a CHANGELOG entry.
- [x] `make gates` green in the worktree.
- [x] Merged to `main`; annotated tag `v0.1.14`; GitHub Release carries the
      sdist and wheel; branch/tag pushed.
- [x] Runtime (`v0.1.0`), assets (`v0.6.0`), ITR/weg/csg and ags-platform
      (`v0.2.0`) pins unchanged.

## Out of scope

- ags-apps internals: the selector fix ships upstream in v0.4.3.
- Runtime v0.2.0 mirror (`REQ-006`, separate ticket/agent).
- Host deployment/provisioning (user-run, later via `dotfiles-v3` PIN-0114).

## Closeout

| Claim | Command | Result |
| --- | --- | --- |
| Red (old pins) | `pytest -q tests/unit/test_verify_role.py::TestVerifyAgsAppsPinMirror::test_engine_consumes_ags_apps_v0_4_3` in a detached worktree at `a30fc9a` | **exit 1** — 1 failed: `AssertionError: the ags_apps role must install ags-apps v0.4.3 … got 'v0.4.2'`; both legs read `v0.4.2` (`ansible/roles/ags_apps/vars/main.yml:102`, `ansible/roles/verify/vars/main.yml:709`). |
| Green (v0.4.3) | same command at `e723622` (HEAD) | **exit 0** — 1 passed in 0.04s. |
| Engine gates | `make gates` at `e723622` | **exit 0** — test 967 passed/32 skipped/54 deselected; hermetic 963 passed/36 skipped/54 deselected; ruff clean; `uv lock --check` resolved 33; docs-check present. |
| Integration | not run | Not required by the release procedure for this XS pin bump: plan section 3.2 names `make gates` only (`/home/inumaki/.opencode/plan/09-release-train.md:50-53`). |
| Pin scope | `git diff v0.1.13..e723622 -- ansible/roles` | Only the two ags-apps lines change (`v0.4.2` → `v0.4.3`). Runtime `v0.1.0`, assets `v0.6.0`, ITR/weg/csg and ags-platform `v0.2.0` are unchanged. |
| Engine version | `rg -n 'version = "0.1.14"|__version__ = "0.1.14"' pyproject.toml src/provisioning/__init__.py`; `uv lock --check` | Both `0.1.14`; lock resolved 33. CHANGELOG has the `[0.1.14] - 2026-10-26` entry. |
| Merge | `git log --oneline --graph` | `b0fc19a` — merge of `d2929fa` (main) + `e723622` (branch); pushed to `origin/main`. |
| Tag | `git show v0.1.14`; `git ls-remote --tags origin 'refs/tags/v0.1.14*'` | Annotated `v0.1.14` → `b0fc19a`; remote peeled `b0fc19a`; pushed. |
| Tag CI | `gh run view 40377829965 --json conclusion,jobs` | `completed/success` — all 8 jobs (test, lint, hermetic, lock-check, docs-check, ci-gates-parity, assets-parity, release). |
| Release assets | `gh release view v0.1.14 --json assets` | `dotfiles_provision-0.1.14-py3-none-any.whl` (244898 bytes), `dotfiles_provision-0.1.14.tar.gz` (442474 bytes); both `uploaded`. |
| Release URL | `gh release view v0.1.14 --json url` | https://github.com/RandomGenericUsername/dotfiles-provision/releases/tag/v0.1.14 |

Post-tag note: `v0.1.14` is immutable and points at `b0fc19a` (implementation +
tests). This closeout commit is docs-only, lands after the tag, and matches the
`v0.1.12`/`v0.1.13` closeout pattern; it changes no packaged file
(`pyproject.toml` packages only `src/provisioning`).

### User host steps (sudo; user-run — the agent must not provision/reboot)

1. In `dotfiles-v3`, this slice deploys through the normal pin flow: advance
   `dotfiles/provisioning/installer.pin` to `v0.1.14` for a standalone deploy,
   or to the final engine tag at `PIN-0114` (planned `v0.1.15`) so the selector
   and runtime palette fixes land together. Commit/push in `dotfiles-v3`.
2. Run the host provision with sudo (become scope installs the ags-apps
   `v0.4.3` unit and repoints the live links):
   `make bootstrap ARGS="--ask-become-pass"` (or `./bootstrap.sh`).
3. Verify the deployed engine and pins:
   `make provision ARGS="--output-format plain verify --expected-engine-tag v0.1.14"`.
4. Selector acceptance (manual): open the wallpaper selector, choose a
   wallpaper, click Apply — the drawer collapses immediately, the apply
   completes, a palette error (if any) surfaces through the notification, and
   reopening the selector works.
5. Rollback if needed: ags-apps units are versioned
   (`<install>/ags-apps/<tag>`); pin `ags_apps_version` /
   `verify_ags_apps_version` to `v0.4.2` in a follow-up engine release and
   re-provision. `v0.1.14` itself is never moved or deleted.
