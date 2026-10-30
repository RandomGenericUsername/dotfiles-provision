---
id: REQ-014
title: "cli_tools: consume the composition manifest as the single pin source"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: none
branch: none
---

# cli_tools: consume the composition manifest as the single pin source

## Requirement

`roles/cli_tools/vars/main.yml` hardcodes the CLI pin list (`cli_tools:` —
csg/weg/itr/tpr/dotfiles-runtime) "mirroring"
`dotfiles/provisioning/cli-tools.yaml`. The manifest is therefore decorative:
bumping it in the composition (PIN-0119, tpr v0.5.0 / runtime v0.5.0) changes
nothing at bootstrap time, and the role silently installs the engine's stale
pins. This is the same source-of-truth defect the palette work is eliminating,
in the provisioning layer.

### Required behavior

1. The role loads its entries from
   `{{ cli_tools_manifests_dir }}/cli-tools.yaml` at run time (the file the
   composition passes through `--manifests-dir`). No hardcoded name/repo/tag
   list remains in the role.
2. Structural validation fails loud before any clone/install: unique `name`,
   safe identifier, exactly one shape per entry (`repo`+`tag` XOR `source`),
   non-empty values.
3. The resolved pins are published as facts for later roles/plays, e.g.
   `cli_tools_tags: {csg: v…, weg: v…, itr: v…, tpr: v…, dotfiles-runtime: v…}`,
   so tag-qualified paths in other manifests (e.g. `assets.yaml` template
   `source`) derive from the pin instead of hardcoding it.
4. The engine's structural parity test is replaced by tests that prove the role
   reads the manifest and rejects malformed manifests — there is nothing left to
   be "at parity" with.
5. Docs/comments stop claiming the hardcoded list mirrors the manifest.

## Acceptance

- [ ] `rg -n 'tag: v0\.' ansible/roles/cli_tools/vars/main.yml` → no pin list.
- [ ] A manifest fixture with distinct tags is what the role resolves (unit/test
      evidence); a malformed manifest fails with a named error.
- [ ] `cli_tools_tags` is set for later plays.
- [ ] Engine gates green; version `0.1.28`, tag released after orchestrator
      review.
- [ ] Live proof: with composition tpr `v0.5.0` / runtime `v0.5.0`, bootstrap
      installs exactly those and `tpr --version` reports `0.5.0`.

## Evidence / Verify

- Evidence: `ansible/roles/cli_tools/vars/main.yml` (`cli_tools:` list),
  composition `dotfiles/provisioning/cli-tools.yaml`; PIN-0119 retry log shows
  the role iterating `tag: v0.4.0` while the manifest says `v0.5.0`.
- Verify: `dotfiles-provision bootstrap` on a host whose composition manifest
  names different tags; `cat $INSTALL/cli-tools/tpr/pinned`.
