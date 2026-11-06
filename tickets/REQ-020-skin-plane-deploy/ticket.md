---
id: REQ-020
title: "Deploy the assets skin plane into the spine and expose the AGS skin pointers"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-020/
branch: ticket/REQ-020-skin-plane-deploy
---

# Deploy the assets skin plane into the spine

## Requirement

The skin plane is implemented and verified in `dotfiles-assets` v0.10.0
(`skins/manifests/{glass,flat,paper}.toml`, `skins/templates/ags.gtk.css.j2`,
`skins/contracts/` vendored at contracts v0.6.0) and `dotfiles-runtime`
v0.8.1 (skin derivation, `cache/skins/<hash>/`, `current/skins/<configDir>.css`,
`current/skin.json`, `desired.json` `skin`). Provisioning must deploy the
skin-class DATA into the install spine where the runtime discovers it, keep the
deployed AGS config dirs linked at their XDG stops, and verify the data shape
without requiring runtime state on a fresh install.

### Chosen spine path

`<install>/skins/` is the canonical deploy target. The runtime resolves skin
manifests/spine inputs in this order (`dotfiles-runtime`
`src/runtime/application/derive.py:245-267`): `<install>/skins`,
`<install>/config/skins`, then `<install>/assets/<tag>/skins`. The first is the
stable spine root, so provisioning mirrors the assets `skins/` class there
(`skins/manifests`, `skins/templates`, `skins/contracts`, `skins/schema.json`,
plus the class's README/tests as inert data). The pinned checkout remains at
`<install>/assets/<tag>/skins` as the fetch-time source, not the contract.

### Consumer pointers

The runtime owns `config/<configDir>/skin.css` and `config/<configDir>/skin.json`
(`dotfiles-runtime` `src/runtime/adapters/consumer_path_spec.py:50-60`;
seeder `src/runtime/adapters/seeder.py:758-775`). Provisioning does NOT create
those pointers and does NOT run the reconcile. It guarantees only:

- the AGS config dir `<install>/config/<configDir>` (owned by
  `ags_apps_units`, not `config_links`/`config_copies`);
- the `$XDG_CONFIG_HOME/<configDir>` -> spine link;
- verify checks the pointers only when they exist.

## Acceptance

- [x] Assets pin mirrors and fixtures move to `dotfiles-assets` v0.10.0; the
      `skins` class is in the class/schema maps and the domain reader.
- [x] `assets` deploys the skins class to `<install>/skins` as a mirrored,
      data-only copy (no code execution, no runtime reconcile).
- [x] `verify` asserts the deployed skin manifests, template, vendored
      contracts/PIN and schema shape, and tolerates absent runtime
      `skin.css`/`skin.json` (checks them only when present).
- [x] AGS spine/XDG links remain owned by `ags_apps_units`; `config_links` and
      `config_copies` do not claim an AGS basename or write into a tag.
- [x] Role/unit tests updated; `make gates` green; engine version and
      CHANGELOG updated; annotated tag created after merge.
- [x] `dotfiles-v3` handoff recorded (engine pin + assets/runtime/platform
      tuple); no `dotfiles-v3` files edited here.

## Evidence / Verify

Branch `ticket/REQ-020-skin-plane-deploy`, worktree `.worktrees/REQ-020/`.
Commits: `d2a1196` (plan), `fc6f013` (implementation + release metadata).

- Runtime discovery: `dotfiles-runtime/src/runtime/application/derive.py:245-267`
  (`_skin_roots` order: `<install>/skins`, `config/skins`,
  `assets/<tag>/skins`) and `:111-129` (`_input_candidates` accepts
  `<install>/skins/templates`).
- Runtime pointers: `dotfiles-runtime/src/runtime/adapters/consumer_path_spec.py:50-60`
  (`config/ags/skin.css` -> `skins/ags.css`, `skin.json` -> `skin.json`);
  seeder `src/runtime/adapters/seeder.py:758-775`. Provisioning writes neither.
- Assets class: `dotfiles-assets/catalog.yaml` (`classes.skins`, tag v0.10.0),
  `skins/contracts/PIN` (`contracts=v0.6.0` + three sha256 values).
- Engine pin mirrors: `rg -n "assets_pinned_tag" ansible/roles` → all
  `v0.10.0`; `rg -n "v0\.6\.4" ansible tests/fixtures` → no matches.
- Chosen spine path: `<install>/skins` (deployed by the `assets` mirror
  `{ name: skins, kind: skins, source: <checkout>/skins/, target: skins }`).
- `make gates` → **rc=0**:
  - `test`: `923 passed, 31 skipped, 52 deselected in 527.86s`
  - `lint`: `All checks passed!`
  - `hermetic`: `920 passed, 34 skipped, 52 deselected in 485.65s`
  - `lock-check`: `Resolved 33 packages in 0.52ms`
  - `docs-check`: rc=0
- `make ci-gates-parity` → PASS
  (`gates=['docs-check','hermetic','lint','lock-check','test']`,
  `jobs=[...,'test']`).
- Corpus-backed parity against the local v0.10.0 checkout:
  `DOTFILES_ASSETS_REPO=/home/inumaki/Development/dotfiles/dotfiles-assets \
   DOTFILES_ASSETS_TEMPLATES_DIR=.../templates \
   uv run pytest -q tests/unit/test_template_vars_parity.py` →
  `10 passed`.
- Real-data verify probe (materialized `<install>/skins` from assets v0.10.0):
  `ANSIBLE_CONFIG=ansible/ansible.cfg ANSIBLE_COLLECTIONS_PATH=$PWD/.collections \
   uv run ansible-playbook -i localhost, -c local /tmp/opencode/req020-verify-skins.yml`
  → `ok=9 changed=0 failed=0`; the PIN sha256 gate and six-group manifest
  checks pass against the real bytes.
- `tests/unit/test_verify_role.py::TestVerifySkinPlane` → both cases pass: a
  valid deployed plane is read-only green; a tampered contract fails the PIN
  gate.
- `make assets-parity` → not runnable in this workspace: it clones the remote
  tag and `v0.10.0` is not published yet (`fatal: Remote branch v0.10.0 not
  found`). The local-corpus parity above is the substitute; publishing the
  assets tag is part of the assets release, not this engine ticket.

## Outcome

Released engine `v0.1.34` (annotated tag created after the fast-forward merge).
The runtime's first skin root is now provisioned by the engine, and a fresh
install verifies green before the first reconcile because the runtime pointers
are optional-when-present.

## Handoff

See the `## Handoff (dotfiles-v3 ticket)` section above: `dotfiles-v3` must
bump `assets.tag` + `program-tuple.yaml` to v0.10.0, add the `skins` class, and
point `installer.pin` at `v0.1.34`. The runtime and ags-platform pins move in
their own parallel tickets. This ticket edited no `dotfiles-v3` file.

## Handoff (dotfiles-v3 ticket)

`dotfiles-v3` still pins assets v0.6.4, its `cli-tools.yaml` runtime pin is
v0.6.1, its program tuple has `ags-platform v0.5.0`, and `installer.pin` is
v0.1.33. The composition ticket must:

1. bump `dotfiles/provisioning/assets.yaml` `assets.tag` to `v0.10.0` and add
   `skins: { dest: skins, schema: skins/schema.json }` plus the `skins` entry;
2. bump `program-tuple.yaml` `dotfiles-assets` to `v0.10.0` and `ags-platform`
   to the parallel ticket's tag; bump `cli-tools.yaml` `dotfiles-runtime` to
   v0.8.1;
3. point `installer.pin` at this engine tag (v0.1.34).

No `dotfiles-v3` file is edited by this ticket.
