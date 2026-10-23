---
id: BUG-001
title: "runtime-seed invokes the deleted composition src/runtime"
kind: bug
status: done
lane: direct
severity: high
links:
  openspec: runtime-seed-installed
  bmad: none
worktree: .worktrees/bug-001/
branch: ticket/bug-001-runtime-seed-installed
repro: "inspect ansible/playbooks/runtime-seed.yaml, then run ./bootstrap.sh from dotfiles-v3 (or wait for runtime-seed in the aggregate)"
observed: "the seed task invokes `uv run --directory {{ composition_root }}/src/runtime dotfiles-runtime wallpaper set …`; `src/runtime/` was deleted by REQ-002, so the seed fails / the bootstrap aborts"
expected: "the seed runs the installed pinned `dotfiles-runtime` from the uv tool bin dir, exactly like the systemd units; no composition source path is read"
---

# runtime-seed invokes the deleted composition `src/runtime`

## Repro

`rg -n 'src/runtime' ansible/playbooks/runtime-seed.yaml` → the argv path.

Then a real bootstrap would reach `runtime-seed` after `cli_tools` installed the pinned runtime and
fail on the missing composition path.

## Observed

`ansible/playbooks/runtime-seed.yaml` still carries:

```yaml
- uv
- run
- --directory
- "{{ composition_root }}/src/runtime"
- dotfiles-runtime
- wallpaper
- set
```

`dotfiles-v3/src/runtime/` was deleted in REQ-002; the runtime is now the pinned
`dotfiles-runtime@v0.1.0` repo. The seed step is the only remaining composition-source read.

## Expected

The seed invokes the installed pinned binary from `runtime_seed_bin_dir`
(`$UV_TOOL_BIN_DIR` → `$XDG_BIN_HOME` → `$HOME/.local/bin`, mirroring `cli_tools_bin_dir` and
`runtime_daemon_bin_dir`), with no `src/runtime` path and no `composition_root` requirement.

## Done-when

- The playbook's command argv starts with `{{ runtime_seed_bin_dir }}/dotfiles-runtime`.
- No `src/runtime` literal remains in `ansible/playbooks/runtime-seed.yaml`.
- A unit test locks the argv and the absence of the composition source path.
- Engine gates green; `v0.1.8` tagged/released; the composition pin bumps to `v0.1.8` in its own
  commit.

## Closeout

| Claim | Command | Result |
| --- | --- | --- |
| No source path remains | `rg -n 'src/runtime|uv run --directory' ansible/playbooks/runtime-seed.yaml` | exit 1, no matches |
| Seed argv locked | `uv run pytest -q tests/unit/test_runtime_seed_playbook.py` | 3 passed |
| Engine gates | `make gates` | `978 passed, 3 skipped, 54 deselected`; lint clean; hermetic `946 passed, 35 skipped, 54 deselected`; lock `Resolved 33 packages` |
| Build | `make build` | `dotfiles_provision-0.1.8-py3-none-any.whl` + `.tar.gz` |
| Seed executes the installed binary | stub `dotfiles-runtime` + `ansible-playbook ansible/playbooks/runtime-seed.yaml` | `ok=4 changed=1 failed=0`; the stub is the only runtime invoked, no composition root needed |
| Main CI | `gh run view 40025470974` | `completed/success` (all gates) |
| Tag CI | `gh run view 40026090029` | `completed/success` incl. `release` |
| Annotated tag | `git rev-parse v0.1.8` / `'v0.1.8^{commit}'` / `git cat-file -t` | `fd2e1f01…` / `9d4648ea…` / `tag` |
| Release artifacts | `gh release view v0.1.8 --json assets` | `dotfiles_provision-0.1.8-py3-none-any.whl`, `dotfiles_provision-0.1.8.tar.gz` |

Composition pin bumped to `v0.1.8` in `dotfiles-v3` commit `291afca0`; its CI is green.
