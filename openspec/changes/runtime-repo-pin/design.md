# Design — runtime as a pinned repo

## D1. The runtime uses the same addressing shape as the CLIs

The runtime is now a public repo at an immutable tag. The engine needs no new install path: the
existing pinned branch already clones `<repo>@<tag>` into
`<install>/cli-tools/<name>/<tag>/`, removes `.git`, writes `pinned`, and runs
`uv tool install --force --no-cache <checkout>` (`roles/cli_tools/tasks/main.yml`). Only the role
mirror and the fixture manifest change.

Evidence: the pinned branch is generic over `cli_tools_pinned`; no task names `dotfiles-runtime`.
Verify: `rg -n "dotfiles-runtime" ansible/roles/cli_tools/tasks/main.yml` → comments only.

## D2. The source-path branch stays, empty

The source-path install/upgrade tasks are the documented extension point for a future in-repo
tool. Removing them would widen this slice and delete a tested capability; leaving them with an
empty loop is a no-op. The tests that asserted "only dotfiles-runtime is a source entry" are
inverted: no entry may carry `source`, while the branch remains.

Evidence: `cli_tools_source_entries` is a `rejectattr('repo', 'defined')` selection, so an all-pinned
list yields `[]`.
Verify: `uv run pytest -q tests/unit/test_cli_tools_role.py -k source`.

## D3. Verify asserts execution, not just `command -v`

`verify` must prove the installed runtime is the tag it mirrors:
- the checkout is `<install>/cli-tools/dotfiles-runtime/<tag>/`;
- `<install>/cli-tools/dotfiles-runtime/pinned` contains exactly the tag;
- `dotfiles-runtime version` exits 0 and prints `0.1.0`.

The runtime has no `--version` flag and no contract token (the contract is consumed by the
`cli-invocation-contract` package, not reported by the binary), so the check uses the `version`
subcommand and the tag without its leading `v`.

Evidence: `dotfiles-runtime version` → `0.1.0` (run in the runtime repo).
Verify: `.venv/bin/dotfiles-runtime version` in `dotfiles-runtime` → `0.1.0`.

## D4. Fixture composition mirrors the live manifest

The engine's tests run against `tests/fixtures/composition/`, not a live `dotfiles-v3` checkout.
The fixture's `cli-tools.yaml` must carry the runtime `{repo, tag}` entry; the `src/runtime`
stub existed only for the source-path shape and is removed.

Evidence: `tests/support.py` resolves the fixture by default; `$DOTFILES_COMPOSITION_ROOT` is the
explicit live override.
Verify: `diff tests/fixtures/composition/dotfiles/provisioning/cli-tools.yaml
dotfiles-v3/dotfiles/provisioning/cli-tools.yaml` → empty after the composition slice.

## D5. Release v0.1.7

The composition consumes the engine as an immutable tag (`installer.pin`). The role/verify change
is only observable after a tag; `v0.1.7` is the release. No PyPI.

Evidence: `dotfiles/provisioning/installer.pin` in the composition reads one semver tag.
Verify: `git tag -l`; `gh release view v0.1.7 --json assets`.

## Verification plan

| Claim | Command | Expected |
| --- | --- | --- |
| All entries pinned | `uv run pytest -q tests/unit/test_cli_tools_role.py` | exit 0 |
| Verify mirrors | `uv run pytest -q tests/unit/test_verify_role.py` | exit 0 |
| Fixture parity | `uv run pytest -q tests/unit/test_cli_tools_role.py -k parity` | exit 0 |
| Full gates | `make gates` | exit 0 |
| Build | `make build` | wheel + sdist |
