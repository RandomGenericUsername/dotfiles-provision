---
id: BUG-002
title: "Installed engine wheel drops inventory/group_vars"
kind: bug
status: done
lane: direct
severity: high
links:
  openspec: group-vars-wheel
  bmad: none
worktree: .worktrees/bug-002/
branch: ticket/bug-002-group-vars-wheel
repro: "uv tool install git+https://github.com/RandomGenericUsername/dotfiles-provision@v0.1.8; then run `make provision ARGS='verify --expected-engine-tag v0.1.8'` from dotfiles-v3"
observed: "verify fails with 'container_runtime_engine' is undefined (and later 'shell' is undefined); the installed _ansible/inventory/ has no group_vars"
expected: "the wheel carries provisioning/_ansible/inventory/group_vars/{all,arch,debian-family}.yml next to the inventory, so every CLI command resolves the declared engine and shell vars"
---

# Installed engine wheel drops `inventory/group_vars`

## Repro

```bash
uv tool install --force "git+https://github.com/RandomGenericUsername/dotfiles-provision@v0.1.8"
cd ~/Development/dotfiles/dotfiles-v3
make provision ARGS="verify --expected-engine-tag v0.1.8"
```

## Observed

```text
'container_runtime_engine' is undefined
```

The installed wheel's `provisioning/_ansible/inventory/` contains only
`localhost.yaml`. The source had `inventory/group_vars -> ../group_vars`, a
symlink the sdist/wheel build silently dropped. `bootstrap.sh` masks this because
it passes the cached engine checkout's inventory; `make provision` uses the
installed wheel's inventory and fails.

## Expected

`ansible/inventory/group_vars/` is a real directory (the canonical location),
the source keeps no `ansible/group_vars` symlink, and the wheel contains all
three group_vars files next to `localhost.yaml`. `make build` asserts it.

## Done-when

- `unzip -l dist/dotfiles_provision-0.1.9-*.whl` lists
  `provisioning/_ansible/inventory/group_vars/{all,arch,debian-family}.yml`.
- `make build` runs the wheel-content check and passes.
- The source tests read `ansible/inventory/group_vars/*`.
- `make gates` green; `v0.1.9` tagged/released; the composition pin bumps to
  `v0.1.9`; a real `make provision ARGS="verify …"` on the host passes.

## Closeout

| Claim | Command | Result |
| --- | --- | --- |
| Source layout | `test -f ansible/inventory/group_vars/all.yml && test ! -e ansible/group_vars` | exit 0 |
| Wheel layout | `make build` | `PASS: dotfiles_provision-0.1.9-py3-none-any.whl carries the Ansible tree + inventory/group_vars` |
| Engine gates | `make gates` | `978 passed, 3 skipped, 54 deselected`; lint clean; hermetic `946 passed, 35 skipped, 54 deselected`; lock `Resolved 33 packages` |
| Main CI | `gh run view 40136647566` | `completed/success` (all gates) |
| Tag CI | `gh run view 40137141868` | `completed/success` incl. `release` |
| Annotated tag | `git rev-parse v0.1.9` / `'v0.1.9^{commit}'` / `git cat-file -t` | `v0.1.9` tag object / `89f32472…` / `tag` |
| Release artifacts | `gh release view v0.1.9 --json assets` | `dotfiles_provision-0.1.9-py3-none-any.whl`, `dotfiles_provision-0.1.9.tar.gz` |
| Host verify | `make provision ARGS="verify --expected-engine-tag v0.1.9"` (from `dotfiles-v3`) | exit 0; all verify tasks ok; engine 0.1.9, runtime 0.1.0 |

Composition pin bumped to `v0.1.9` in `dotfiles-v3` commit `e0a83b8a`; its CI is green.
