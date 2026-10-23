# runtime-repo-pin

## Why

`dotfiles-runtime` is now its own repo at `RandomGenericUsername/dotfiles-runtime`, tagged
`v0.1.0` with history preserved from `dotfiles-v3/src/runtime`. The engine still describes it as
the composition's one in-repo `source:` entry (`src/runtime`), which is false after the extraction
and blocks the composition from deleting the tree.

Evidence: the runtime repo's `v0.1.0` release is public and its `main` CI is green
(`gh release view v0.1.0 -R RandomGenericUsername/dotfiles-runtime`).
Verify: `git ls-remote https://github.com/RandomGenericUsername/dotfiles-runtime 'refs/tags/v0.1.0'`
→ one line.

## What Changes

- Mirror `dotfiles-runtime` as `{name, repo, tag: v0.1.0}` in
  `roles/cli_tools/vars/main.yml`; all four CLI entries become pinned.
- Add `dotfiles-runtime` to `verify_cli_tools` and add the runtime checkout/pin/version variables.
- Add the runtime verify block: tag-bearing checkout + `pinned` record + `dotfiles-runtime version`
  = `0.1.0`.
- Keep the source-path install branch (it remains the extension point for a future in-repo tool)
  but its loop now selects nothing. Update the comments and tests that describe the mixed shape.
- Refresh the fixture composition manifest and retire the `src/runtime` stub.
- Release `v0.1.7` so the composition can pin the engine tag.

## Capabilities

- **New Capabilities:** `runtime-consumption` — the engine treats the runtime as a pinned CLI.
- **Modified Capabilities:** none for `csg`/`weg`/`itr`; their pins, tasks and images are unchanged.

## Non-goals

- The composition's pin bump, `src/runtime/` deletion, gate retirement, docs/spec updates. Those
  land in `dotfiles-v3` after `v0.1.7`.
- Any change to the runtime package or its `v0.1.0` tag.
- Adding a container image for the runtime.

## Impact

- Modified: `ansible/roles/cli_tools/vars/main.yml`, `ansible/roles/verify/{vars,tasks}/main.yml`,
  `tests/fixtures/composition/dotfiles/provisioning/cli-tools.yaml`,
  `tests/unit/test_cli_tools_role.py`, `tests/unit/test_verify_role.py`,
  `tests/fixtures/composition/README.md`, `tests/support.py`, `ansible/group_vars/all.yml`,
  `src/provisioning/{application/use_cases.py,cli/options.py}`, `README.md`, `AGENTS.md`,
  `pyproject.toml`, `CHANGELOG.md`.
- Removed: `tests/fixtures/composition/src/runtime/pyproject.toml`.
- Unchanged: every role task that installs `csg`/`weg`/`itr`, every image build, every manifest
  shape except the runtime entry.
