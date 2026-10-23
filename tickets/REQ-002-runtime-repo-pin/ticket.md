---
id: REQ-002
title: "Consume dotfiles-runtime as a pinned repo (engine v0.1.7)"
kind: requirement
status: done
lane: 3
links:
  openspec: runtime-repo-pin
  bmad: none
worktree: .worktrees/req-002/
branch: ticket/req-002-runtime-repo-pin
---

# Consume dotfiles-runtime as a pinned repo (engine v0.1.7)

## Requirement

`dotfiles-runtime` was extracted to `RandomGenericUsername/dotfiles-runtime` and tagged
`v0.1.0`. The engine SHALL consume it exactly like `csg`/`weg`/`itr`: a `{name, repo, tag}` entry
in the manifest mirror, installed from the tag-bearing checkout, with `verify` asserting the
checkout path, the `pinned` record and the installed version.

This is the engine-side prerequisite for the composition's destructive-last slice. It changes no
provisioning behaviour for the three existing CLIs and no manifest shape beyond the runtime entry.

## Acceptance

- [x] `roles/cli_tools/vars/main.yml` mirrors `dotfiles-runtime` as
  `{repo: https://github.com/RandomGenericUsername/dotfiles-runtime, tag: v0.1.0}`; no entry carries
  `source`.
- [x] `roles/verify/vars/main.yml` lists `dotfiles-runtime` in `verify_cli_tools` and carries
  `verify_runtime_version` / `verify_runtime_checkout` / `verify_runtime_pin_file` /
  `verify_runtime_tool_version`.
- [x] `verify` asserts the tag-bearing checkout, the `pinned` record and
  `dotfiles-runtime version` = `0.1.0`.
- [x] The source-path install branch remains present and check-mode-safe; its loop is empty.
- [x] The fixture composition mirrors the new manifest; the runtime stub is retired.
- [x] `make gates` green; `make test` counts recorded in the closeout.
- [x] Annotated `v0.1.7` tag + Release with the sdist/wheel; `main` CI green.
- [x] The composition pin (`installer.pin` → `v0.1.7`) is a separate commit in `dotfiles-v3`.

## Out of scope

- Changing `dotfiles-v3` (manifest entry, deletion of `src/runtime/`, gates/docs). That is the
  composition's destructive-last slice.
- Changing runtime behaviour or its package. The runtime repo is already tagged `v0.1.0`.
- Making the runtime a container-mode CLI; it has no image.

## Closeout

| Claim | Command | Result |
| --- | --- | --- |
| Local gates | `make gates` | `975 passed, 3 skipped, 54 deselected`; lint `All checks passed!`; hermetic `943 passed, 35 skipped, 54 deselected`; lock `Resolved 33 packages`; exit 0 |
| Build | `make build` | `dotfiles_provision-0.1.7-py3-none-any.whl` + `.tar.gz` |
| OpenSpec | `openspec validate --all --strict` | 3 passed (repo-birth, repo-harness, runtime-repo-pin) |
| Main CI | `gh run view 40012228224` | `completed/success` (hermetic, ci-gates-parity, assets-parity, docs-check, lock-check, lint, test) |
| Tag CI | `gh run view 40013439917` | `completed/success` after one re-run; the first hermetic attempt died on a transient `IncompleteRead` while installing Ansible collections, not a code failure |
| Annotated tag | `git rev-parse v0.1.7` / `'v0.1.7^{commit}'` / `git cat-file -t` | `506fa1d5eab…` / `bb11d21927…` / `tag` |
| Anonymous fetch | `GIT_TERMINAL_PROMPT=0 git -c credential.helper= ls-remote … 'refs/tags/v0.1.7'` | one line, `506fa1d… refs/tags/v0.1.7` |
| Release artifacts | `gh release view v0.1.7 --json assets` | `dotfiles_provision-0.1.7-py3-none-any.whl`, `dotfiles_provision-0.1.7.tar.gz` |

The composition's `installer.pin` → `v0.1.7`, its manifest entry, deletion of `src/runtime/`
and the runtime-only gates are the destructive-last slice in `dotfiles-v3`.
