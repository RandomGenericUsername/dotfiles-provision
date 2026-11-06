---
id: REQ-021
title: "Consume dotfiles-assets v0.11.0 (per-app skin templates)"
kind: requirement
status: proposed
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-021/
branch: ticket/REQ-021-skins-assets-v011
---

# Consume dotfiles-assets v0.11.0

## Requirement

REQ-020 deployed the `skins` class from `dotfiles-assets` v0.10.0 and verified
one template. v0.11.0 adds six per-app templates beside the bar template:
`ags-clipboard`, `ags-notifications`, `ags-wallpaper-selector`, `ags-capture`,
`ags-icme` and `ags-btop-studio`, for seven templates total. Every assets pin
mirror and composition fixture moves to v0.11.0, and verify must prove the
deployed `<install>/skins` plane carries all seven templates, the v1 manifest
shape and token placeholders that resolve against every manifest, plus the
vendored contracts pinned at `contracts` v0.6.0.

## Acceptance

- [ ] Every `*_assets_pinned_tag` mirror is `v0.11.0`; the composition fixture
      `assets.yaml` (tag + checkout sources) and `program-tuple.yaml` follow.
- [ ] The `assets` role still mirrors the `skins/` class to `<install>/skins`
      as data only; `assets_classes` and the manifest reader accept the sixth
      class with the new tag.
- [ ] Verify asserts all seven `<configDir>.gtk.css.j2` templates, the three
      manifests keep `schema_major`, `name`, `hairline-w` and the six groups,
      every template placeholder resolves against every manifest, and the
      vendored contracts re-hash against the v0.6.0 PIN.
- [ ] Runtime-owned `config/<configDir>/skin.{css,json}` checks stay tolerant
      of absence on a fresh install and still reject a present non-`current/`
      pointer.
- [ ] Tests cover seven templates and the v0.11.0 pin; a tampered template or
      contract fails.
- [ ] `make gates`, `make ci-gates-parity` and the local-corpus
      `test_template_vars_parity.py` pass; engine `0.1.35` + CHANGELOG.
- [ ] Annotated tag `v0.1.35` after the fast-forward merge; no push.

## Evidence / Verify

Evidence recorded when the implementation commit lands.
