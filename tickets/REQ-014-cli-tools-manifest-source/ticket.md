---
id: REQ-014
title: "cli_tools: consume the composition manifest as the single pin source"
kind: requirement
status: in-progress
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-014/
branch: ticket/REQ-014-cli-tools-manifest-source
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

- [x] `rg -n 'tag: v0\.' ansible/roles/cli_tools/vars/main.yml` → no pin list.
- [x] A manifest fixture with distinct tags is what the role resolves (unit/test
      evidence); a malformed manifest fails with a named error.
- [x] `cli_tools_tags` is set for later plays.
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

## Progress

- [x] Role loads `{{ cli_tools_manifests_dir }}/cli-tools.yaml` at run time
      (`vars/main.yml` lookup → `cli_tools`); the hardcoded pin list is gone.
- [x] `tasks/manifest.yml` validates kind, non-empty entries, unique safe
      names, one shape per entry (`source` XOR `repo` + `tag`) and non-empty
      values before any clone/install; errors name the entry and field.
- [x] `cli_tools_tags` (name → tag) is published with `set_fact` for later
      plays; role comments document it as the composition's tag-path mechanism.
- [x] Structural parity test replaced by real `ansible-playbook` fixture runs:
      arbitrary distinct tags resolve, malformed manifests fail named.
- [x] Verify/assets/settings pin-mirror tests now compare against the manifest
      the role reads; docs/comments no longer claim a hardcoded mirror.
- [x] Engine version `0.1.28` + CHANGELOG entry; no tag/push.

## Evidence

- No pin list: `rg -n 'tag: v0\.' ansible/roles/cli_tools/vars/main.yml` →
  exit 1, no output.
- Run-time resolution: `uv run --frozen pytest -q
  tests/unit/test_cli_tools_role.py` → `53 passed`; the new
  `TestCliToolsManifestSource` runs the role's real var-load + validation tasks
  with a fixture manifest (`csg v9.9.1`, `weg v8.8.2`) and asserts
  `cli_tools_tags` equals those values.
- Named failures: same class parameterizes duplicate name, both shapes, missing
  tag, unsafe name, missing kind and empty entries; each asserts the entry/field
  text in the Ansible failure.
- Regression legs: `uv run --frozen pytest -q
  tests/unit/test_verify_role.py` → `122 passed`; `uv run --frozen pytest -q
  tests/unit/test_template_vars_parity.py` → `9 passed, 2 skipped`.
- Version: `pyproject.toml`, `src/provisioning/__init__.py` and `uv.lock` are
  `0.1.28` (`uv lock` → `Updated dotfiles-provision v0.1.27 -> v0.1.28`).
- Gates: `make gates` → exit 0 — `test` `953 passed, 3 skipped, 60 deselected`;
  `lint` `All checks passed!`; `hermetic` `922 passed, 34 skipped, 60
  deselected`; `lock-check` `Resolved 33 packages`; `docs-check` silent (pass).
  `make ci-gates-parity` → `PASS gates=[...] jobs=[...]`.
- OpenSpec: `openspec validate --all --strict` → `4 passed, 0 failed`.

## Deviations / risks

- `cli_tools_tags` covers pinned (`repo` + `tag`) entries only; source entries
  have no tag by definition. The role keeps the source-path install branch as
  an extension point, but today the composition fixture has no source entry.
- The assets manifest still owns its own `assets_*_pinned_tag` mirrors; this
  ticket only documents `cli_tools_tags` as the available mechanism, it does
  not rewrite the composition-owned `assets.yaml` sources.
