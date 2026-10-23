# runtime-seed-installed

## Why

`v0.1.7` moved `dotfiles-runtime` to a pinned repo, but `ansible/playbooks/runtime-seed.yaml`
still runs `uv run --directory {{ composition_root }}/src/runtime dotfiles-runtime …`. The
composition deleted `src/runtime/` in its destructive-last slice, so a fresh bootstrap (or any
apply) now fails at the seed step after `cli_tools` has installed the pinned runtime.

Evidence: `ansible/playbooks/runtime-seed.yaml:51-61` (the argv); `dotfiles-v3` commit `62904e4c`
deletes `src/runtime/`.
Verify: `rg -n 'src/runtime' ansible/playbooks/runtime-seed.yaml`.

## What Changes

- Add a play-level `runtime_seed_bin_dir` resolved exactly as uv does
  (`$UV_TOOL_BIN_DIR` → `$XDG_BIN_HOME` → `$HOME/.local/bin`), mirroring
  `cli_tools_bin_dir` / `runtime_daemon_bin_dir`.
- Invoke `{{ runtime_seed_bin_dir }}/dotfiles-runtime wallpaper set <install>/wallpapers/default.png`.
- Drop the seed play's `composition_root` assert and the `src/runtime` comment; the seed no longer
  reads a composition source path.
- Add a unit test locking the installed-binary argv and the absence of `src/runtime`.
- Release `v0.1.8`; the composition bumps its installer pin in its own commit.

## Capabilities

- **Modified Capabilities:** `runtime-consumption` — the seed step is part of consuming the pinned
  runtime.

## Non-goals

- No change to the runtime package or its `v0.1.0` tag.
- No change to the composition manifests beyond the installer pin bump.
- No change to `runtime-seed`'s ordering or check-gating.

## Impact

- Modified: `ansible/playbooks/runtime-seed.yaml`, `tests/unit/test_bootstrap_playbook.py` (or a
  new focused test), `pyproject.toml`, `CHANGELOG.md`, this change, the bug ticket.
- Unchanged: the runtime, the composition, every other role/playbook.
