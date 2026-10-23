---
id: REQ-002
title: "Consume dotfiles-runtime as a pinned repo (engine v0.1.7)"
kind: requirement
status: in-progress
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

- [ ] `roles/cli_tools/vars/main.yml` mirrors `dotfiles-runtime` as
  `{repo: https://github.com/RandomGenericUsername/dotfiles-runtime, tag: v0.1.0}`; no entry carries
  `source`.
- [ ] `roles/verify/vars/main.yml` lists `dotfiles-runtime` in `verify_cli_tools` and carries
  `verify_runtime_version` / `verify_runtime_checkout` / `verify_runtime_pin_file` /
  `verify_runtime_tool_version`.
- [ ] `verify` asserts the tag-bearing checkout, the `pinned` record and
  `dotfiles-runtime version` = `0.1.0`.
- [ ] The source-path install branch remains present and check-mode-safe; its loop is empty.
- [ ] The fixture composition mirrors the new manifest; the runtime stub is retired.
- [ ] `make gates` green; `make test` counts recorded in the closeout.
- [ ] Annotated `v0.1.7` tag + Release with the sdist/wheel; `main` CI green.
- [ ] The composition pin (`installer.pin` → `v0.1.7`) is a separate commit in `dotfiles-v3`.

## Out of scope

- Changing `dotfiles-v3` (manifest entry, deletion of `src/runtime/`, gates/docs). That is the
  composition's destructive-last slice.
- Changing runtime behaviour or its package. The runtime repo is already tagged `v0.1.0`.
- Making the runtime a container-mode CLI; it has no image.
