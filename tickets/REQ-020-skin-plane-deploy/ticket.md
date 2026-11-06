---
id: REQ-020
title: "Deploy the assets skin plane into the spine and expose the AGS skin pointers"
kind: requirement
status: in-progress
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

- [ ] Assets pin mirrors and fixtures move to `dotfiles-assets` v0.10.0; the
      `skins` class is in the class/schema maps and the domain reader.
- [ ] `assets` deploys the skins class to `<install>/skins` as a mirrored,
      data-only copy (no code execution, no runtime reconcile).
- [ ] `verify` asserts the deployed skin manifests, template, vendored
      contracts/PIN and schema shape, and tolerates absent runtime
      `skin.css`/`skin.json` (checks them only when present).
- [ ] AGS spine/XDG links remain owned by `ags_apps_units`; `config_links` and
      `config_copies` do not claim an AGS basename or write into a tag.
- [ ] Role/unit tests updated; `make gates` green; engine version and
      CHANGELOG updated; annotated tag created after merge.
- [ ] `dotfiles-v3` handoff recorded (engine pin + assets/runtime/platform
      tuple); no `dotfiles-v3` files edited here.

## Evidence / Verify

Evidence is recorded on the ticket branch as the implementation commits land.

- Runtime discovery: `dotfiles-runtime/src/runtime/application/derive.py:245-267`
  (`_skin_roots`) and `:111-129` (`_input_candidates` skin templates).
- Runtime pointers: `dotfiles-runtime/src/runtime/adapters/consumer_path_spec.py:50-60`,
  `src/runtime/adapters/seeder.py:758-775`.
- Assets class: `dotfiles-assets/catalog.yaml` (`classes.skins`, tag v0.10.0),
  `skins/contracts/PIN` (`contracts=v0.6.0` + three sha256 values).
- Engine pin mirrors: `rg -n "_assets_pinned_tag|assets_pinned_tag" ansible/roles`.
- Verify: `make gates`; targeted role suites as listed in the closeout commit.

## Handoff (dotfiles-v3 ticket)

`dotfiles-v3` still pins assets v0.6.4, runtime v0.8.1 is not in its program
tuple, and `installer.pin` is v0.1.33. The composition ticket must:

1. bump `dotfiles/provisioning/assets.yaml` `assets.tag` to `v0.10.0` and add
   `skins: { dest: skins, schema: skins/schema.json }` plus the `skins` entry;
2. bump `program-tuple.yaml` `dotfiles-assets` to `v0.10.0` and its runtime /
   platform pins as the parallel tickets land;
3. point `installer.pin` at this engine tag (v0.1.34).

No `dotfiles-v3` file is edited by this ticket.
