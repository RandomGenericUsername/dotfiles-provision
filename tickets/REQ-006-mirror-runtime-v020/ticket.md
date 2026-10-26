---
id: REQ-006
title: "Mirror runtime v0.2.0 in verify + release v0.1.15"
kind: requirement
status: in-progress
lane: 1
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-006/
branch: ticket/REQ-006-mirror-runtime-v020
---

# REQ-006 — Mirror runtime v0.2.0 in verify + release v0.1.15

## Requirement

The engine SHALL consume `dotfiles-runtime` `v0.2.0` (mandatory-palette
release, BUG-001) and SHALL assert the same version in `verify`. Concretely:

- `verify_runtime_version` moves `v0.1.0` → `v0.2.0`;
- `verify_runtime_tool_version` moves `0.1.0` → `0.2.0`;
- the existing runtime pin mirror (`cli_tools` role tag + fixture composition
  manifest) moves in lockstep, because the repo's parity tests lock
  role == verify == fixture;
- a red version-mirror guard fails at `v0.1.0` and passes at `v0.2.0`;
- the CHANGELOG records the bump and the engine is released as annotated tag
  `v0.1.15` with a GitHub Release carrying the sdist and wheel.

No ags-apps or assets pin moves. No new runtime install pin is added here.

## Pin / source evidence

- Upstream tag exists and resolves to the expected peeled commit:

  ```text
  $ git ls-remote --tags https://github.com/RandomGenericUsername/dotfiles-runtime 'refs/tags/v0.2.0*'
  64368a0ebe81d9dab50e57d35ad35dd181e8f725	refs/tags/v0.2.0
  376be9f7399961e27857e7bc6bb6f974e61faf58	refs/tags/v0.2.0^{}
  ```

  The peeled commit `376be9f` is the expected target (annotated tag object
  `64368a0`). Evidence: command output above.
  Verify: `git ls-remote --tags https://github.com/RandomGenericUsername/dotfiles-runtime 'refs/tags/v0.2.0*'`.

- Upstream release metadata:

  ```text
  $ gh release view v0.2.0 --repo RandomGenericUsername/dotfiles-runtime \
      --json tagName,name,publishedAt,url,assets
  {"assets":["dotfiles_runtime-0.2.0-py3-none-any.whl","dotfiles_runtime-0.2.0.tar.gz"],
   "name":"dotfiles-runtime v0.2.0",
   "publishedAt":"2026-10-26T15:54:49Z",
   "tagName":"v0.2.0",
   "url":"https://github.com/RandomGenericUsername/dotfiles-runtime/releases/tag/v0.2.0"}
  ```

  Evidence: quoted `gh` output; URL above.
  Verify: `gh release view v0.2.0 --repo RandomGenericUsername/dotfiles-runtime --json tagName,name,url`.

- Current engine pins (all `v0.1.0` / `0.1.0`):

  ```text
  $ rg -n 'tag: v0\.1\.0|verify_runtime_version: v0\.1\.0|verify_runtime_tool_version: 0\.1\.0' \
      ansible/roles/cli_tools/vars/main.yml ansible/roles/verify/vars/main.yml \
      tests/fixtures/composition/dotfiles/provisioning/cli-tools.yaml
  ansible/roles/cli_tools/vars/main.yml:130:    tag: v0.1.0
  ansible/roles/verify/vars/main.yml:336:verify_runtime_version: v0.1.0
  ansible/roles/verify/vars/main.yml:337:verify_runtime_tool_version: 0.1.0
  tests/fixtures/composition/dotfiles/provisioning/cli-tools.yaml:22:    tag: v0.1.0
  ```

  Evidence: command output above.
  Verify: same command.

- Release-train scope: `.opencode/plan/09-release-train.md:55-58` (section 3.3)
  names `REQ-006-mirror-runtime-v020 → v0.1.15`, precondition runtime v0.2.0,
  change `verify_runtime_version` + `verify_runtime_tool_version`, `make gates`,
  tag + release. Section 4 (lines 60-66) assigns the composition manifest bump
  (`dotfiles-v3/dotfiles/provisioning/cli-tools.yaml`) to `PIN-0114`.
  Evidence: file path + line range above.
  Verify: `sed -n '55,66p' /home/inumaki/.opencode/plan/09-release-train.md`.

## Triage

Per `.opencode/commands/triage.md`:

- `kind: requirement` — the request is "consume upstream release v0.2.0 in the
  engine", a bounded pin/behavior mirror (not a bug in this repo, not an epic,
  no parent).
- `lane: 1` — XS direct. Fully understood: four mirrored literals, the existing
  parity/execution tests, CHANGELOG, engine version and the standard release
  procedure. The palette fix itself ships in `dotfiles-runtime`; this repo has
  no OpenSpec capability delta (`links.openspec: none`).
- No ambiguity to resolve; BMAD is not invoked.

Evidence: this ticket's pin/source section + the `rg` output above.
Verify: `rg -n "^kind: requirement|^lane: 1" tickets/REQ-006-mirror-runtime-v020/ticket.md`.

### Scope note — engine-side mirror vs composition install pin

`verify` is hand-mirrored to the `cli_tools` role by
`TestVerifyRuntimePinMirror` / `test_itr_pin_mirrors_the_cli_tools_role`, and the
role is hand-mirrored to the composition fixture by
`test_cli_tools_parity_with_manifest`. Leaving the engine-side install pin at
`v0.1.0` while verify demands `v0.2.0` would make `make gates` red and the final
verify unsatisfiable (it would require a version the engine never installs).
The engine-side literals therefore move together; **no new pin location is
added**, and the real composition manifest
(`dotfiles-v3/dotfiles/provisioning/cli-tools.yaml`) is untouched — that is
`PIN-0114`'s change.

## Acceptance

- [x] A red version-mirror guard fails at `v0.1.0` and passes at `v0.2.0`.
- [x] `verify_runtime_version: v0.2.0` and `verify_runtime_tool_version: 0.2.0`.
- [x] The `cli_tools` role tag and the fixture composition manifest mirror both
      say `v0.2.0`; the existing literal assertions are updated.
- [x] Engine version `0.1.15` (`pyproject.toml`, `src/provisioning/__init__.py`,
      `uv.lock`) and a CHANGELOG entry.
- [x] `make gates` green in the worktree; `make test-integration` not required
      by release-train section 3.3 (it names `make gates` only).
- [ ] Merged to `main`; annotated tag `v0.1.15`; GitHub Release carries the
      sdist and wheel; branch/tag pushed.
- [x] ags-apps (`v0.4.3`), assets (`v0.6.0`), ITR/weg/csg and ags-platform
      (`v0.2.0`) pins unchanged.

## Out of scope

- `dotfiles-v3` (`cli-tools.yaml` runtime tag, `installer.pin`) — `PIN-0114`,
  separate agent/repo.
- Host provisioning/reboot (user-run, sudo; see host note below).
- Runtime internals: the mandatory-palette behavior ships upstream in v0.2.0.

## Host note (user-run)

`verify` will only pass on a host that already has runtime `v0.2.0` installed.
This release does not provision any host: the final deploy installs the runtime
through `dotfiles-v3` `PIN-0114` (engine `v0.1.15` + `cli-tools.yaml` runtime
`v0.2.0`). Until that pin is deployed, `verify` on an old host is expected to
fail on the runtime leg by design.

## Closeout

| Claim | Command | Result |
| --- | --- | --- |
| Red (old pins) | `uv run pytest -q tests/unit/test_verify_role.py::TestVerifyRuntimePinMirror` at `a22b06e` | **exit 1** — 1 failed, 1 passed: `AssertionError: the cli_tools role must install dotfiles-runtime v0.2.0 (mandatory palette); got 'v0.1.0'` (`ansible/roles/cli_tools/vars/main.yml:130`). |
| Green (v0.2.0) | same command at `47af8bf` | **exit 0** — 2 passed in 0.25s. |
| Related pins | `uv run pytest -q tests/unit/test_verify_role.py::TestVerifyVars::test_runtime_pin_is_asserted_by_execution tests/unit/test_verify_role.py::TestVerifyVars::test_itr_pin_mirrors_the_cli_tools_role tests/unit/test_cli_tools_role.py::TestCliToolsPinnedCheckout` | **exit 0** — 3 passed. Parity `test_cli_tools_parity_with_manifest` + the pinned-checkout class → 9 passed. |
| Engine gates | `make gates` at `47af8bf` | **exit 0** — test 969 passed/32 skipped/54 deselected; lint all checks passed; hermetic 965 passed/36 skipped/54 deselected; `uv lock --check` resolved 33; docs-check present. |
| Integration | not run | Release-train section 3.3 names `make gates` only (`/home/inumaki/.opencode/plan/09-release-train.md:55-58`). |
| Pin scope | `git diff v0.1.14..47af8bf -- ansible/roles` | Only the runtime literals change (`v0.1.0` → `v0.2.0`); ags-apps `v0.4.3`, assets `v0.6.0`, ITR/weg/csg and ags-platform `v0.2.0` unchanged. |
| Engine version | `rg -n 'version = "0.1.15"\|__version__ = "0.1.15"' pyproject.toml src/provisioning/__init__.py`; `uv lock --check` | `pyproject.toml:3`, `src/provisioning/__init__.py:6`, `uv.lock:238` all `0.1.15`; lock resolved 33. CHANGELOG has `[0.1.15] - 2026-10-26`. |
| Merge | pending | pending |
| Tag | pending | pending |
| Release assets | pending | pending |
| Release URL | pending | pending |

Evidence: commands and observed results in the table above, run in
`.worktrees/REQ-006/` on the listed commits.
Verify: re-run the red/green commands and `make gates` from the worktree.

### User host steps (sudo; user-run — the agent must not provision/reboot)

1. In `dotfiles-v3`, land `PIN-0114`: `dotfiles/provisioning/cli-tools.yaml`
   runtime tag `v0.2.0` and `installer.pin` `v0.1.15`.
2. Run the host provision with sudo (`./bootstrap.sh` or
   `make bootstrap ARGS="--ask-become-pass"`), then reboot.
3. Verify: `make provision ARGS="--output-format plain verify --expected-engine-tag v0.1.15"`.
