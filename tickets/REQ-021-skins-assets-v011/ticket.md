---
id: REQ-021
title: "Consume dotfiles-assets v0.11.0 (per-app skin templates)"
kind: requirement
status: done
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

- [x] Every `*_assets_pinned_tag` mirror is `v0.11.0`; the composition fixture
      `assets.yaml` (tag + checkout sources) and `program-tuple.yaml` follow.
- [x] The `assets` role still mirrors the `skins/` class to `<install>/skins`
      as data only; `assets_classes` and the manifest reader accept the sixth
      class with the new tag.
- [x] Verify asserts all seven `<configDir>.gtk.css.j2` templates, the three
      manifests keep `schema_major`, `name`, `hairline-w` and the six groups,
      every template placeholder resolves against every manifest, and the
      vendored contracts re-hash against the v0.6.0 PIN.
- [x] Runtime-owned `config/<configDir>/skin.{css,json}` checks stay tolerant
      of absence on a fresh install and still reject a present non-`current/`
      pointer.
- [x] Tests cover seven templates and the v0.11.0 pin; a tampered template or
      contract fails.
- [x] `make gates`, `make ci-gates-parity` and the local-corpus
      `test_template_vars_parity.py` pass; engine `0.1.35` + CHANGELOG.
- [x] Annotated tag `v0.1.35` after the fast-forward merge; no push.

## Evidence / Verify

Branch `ticket/REQ-021-skins-assets-v011`, worktree `.worktrees/REQ-021/`.
Commits: `7129eef` (plan), `76c1cbd` (implementation + release metadata).

- Pin mirrors: `rg -n 'v0\.10\.0' ansible tests/fixtures` → no matches (the
  only remaining v0.10.0 text is the historical reader comment recording when
  `skins` joined); `rg -n 'assets_pinned_tag:' ansible/roles/*/vars/main.yml`
  → all `v0.11.0`.
- Corpus: local `dotfiles-assets` tag `v0.11.0` ships seven templates under
  `skins/templates/` (bar + the six per-app targets) and keeps
  `skins/contracts/PIN` at `contracts=v0.6.0` with three sha256 values.
- `make gates` → **rc=0**:
  - `test`: `926 passed, 31 skipped, 52 deselected in 584.63s`
  - `lint`: `All checks passed!`
  - `hermetic`: `923 passed, 34 skipped, 52 deselected in 538.25s`
  - `lock-check`: `Resolved 33 packages in 0.75ms`
  - `docs-check`: rc=0
- `make ci-gates-parity` → **PASS**
  (`gates=['docs-check','hermetic','lint','lock-check','test']`,
  `jobs=[...,'test']`, exempt `assets-parity, ci-gates-parity, release`).
- Local-corpus template parity (no remote clone; assets v0.11.0 is local-only):
  `DOTFILES_ASSETS_REPO=/home/inumaki/Development/dotfiles/dotfiles-assets    DOTFILES_ASSETS_TEMPLATES_DIR=.../templates    uv run pytest -q tests/unit/test_template_vars_parity.py` → `10 passed`.
- Real-data skin probe against a materialized `<install>/skins` copied from
  the local v0.11.0 corpus:
  `ansible-playbook -i localhost, -c local /tmp/opencode/req021-verify-skins.yml`
  → `ok=10 changed=0 failed=0` (seven templates + 24-token manifests + PIN
  sha256 all pass).
- Verify tests: `TestVerifySkinPlane` covers the green plane, a missing
  per-app template, a template naming an unknown `SKIN_*` token, and a
  tampered vendored contract. The existing assets pin/schema tests stay green
  at v0.11.0. The AGS pointer tasks remain optional-when-present; the
  integration suite (`TestVerifyRuntime`, 12 passed) proves absent pointers
  do not fail a fresh standalone-app install.
- `make test-integration`-class probe:
  `pytest -q tests/unit/test_verify_role.py::TestVerifyRuntime -m integration`
  → `12 passed in 647.53s`.

## Outcome

Released engine `v0.1.35` (annotated tag created after the fast-forward
merge). The deployed skin plane now verifies all seven v0.11.0 templates and
their placeholders against every manifest.

## Handoff (dotfiles-v3 ticket)

Exact values for the composition ticket:

- `dotfiles/provisioning/installer.pin`: `v0.1.35`
- `dotfiles/provisioning/assets.yaml`: `assets.tag: v0.11.0` and all four
  checkout sources under `assets/v0.11.0/`
- `dotfiles/provisioning/cli-tools.yaml`: `dotfiles-runtime: v0.8.1` (the
  skin-aware runtime; this engine ticket does not move the tool pin)
- `dotfiles/provisioning/program-tuple.yaml`: `ags-platform: v0.5.0`,
  `contracts: v0.3.0`, `dotfiles-assets: v0.11.0`

No `dotfiles-v3` file is edited by this ticket.
