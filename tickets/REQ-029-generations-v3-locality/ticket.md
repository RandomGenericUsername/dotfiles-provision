---
id: REQ-029
title: "Deploy v3 state locality: immutable app tags and stable consumer links"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-029/
branch: ticket/REQ-029-generations-v3-locality
---

# Deploy v3 state locality: immutable app tags and stable consumer links

## Requirement

Generations v3 (`dotfiles-v3/docs/107-generations-v3.md` §2.7, contracts
`generations.md` v0.8.0 §6) moves every runtime write under
`$XDG_STATE_HOME/dotfiles/` and makes `<install>/apps/<installDir>/<tag>` an
immutable app tag. The engine must stop expecting runtime files inside a tag or
inside an app's config spine link, provide provisioning-owned stable links for
the non-runtime palette consumers (`gtk-3.0`, `gtk-4.0`, `rofi`, `btop`) that
resolve through `current/palette/...`, and verify the generation manifest plus
the immutability boundary. App runtime sheets are read by the app from
`state/current/appearance/<configDir>.css`; provisioning never copies or links
them through a tag.

Fresh-install absence stays tolerated: provisioning creates only stable links,
and verify rejects a runtime artifact only when one is actually present.

## Acceptance

- [x] `state_links` role creates the four provisioning-owned stable consumer
      links in `<install>/config/{gtk-3.0,gtk-4.0,rofi,btop}` pointing at
      `$XDG_STATE_HOME/dotfiles/current/palette/...`; it never writes through
      an AGS app spine link or into a tag.
- [x] `wlogout` reads the palette directly from
      `state/current/palette/colors.gtk.css`; no `config/ags/colors.css`
      runtime pointer is required.
- [x] `runtime-seed` asserts a committed v3 generation
      (`current/manifest.json`, `version: 3`, hash == current target) instead of
      v2 consumer links under the install spine.
- [x] `ags_apps_units` removes stale runtime artifacts
      (`appearance.css`, `skin.css`, `skin.json`, `tokens.json`, `colors*`)
      from an existing tag on reinstall/rollback and verifies none remain.
- [x] `verify` asserts the generation manifest/current hash and
      `current/appearance/<configDir>.css` targets when present, verifies the
      stable consumer links resolve through `current/palette/`, and fails when
      a runtime artifact is planted in any app tag.
- [x] The engine expects contracts `v0.8.0` where it validates the generation
      schema/PIN, and the fixture suite carries the vendored schema/PIN.
- [x] Role tests cover immutable app installs, stable consumer links,
      absent-state tolerance and generation-manifest verification.
- [x] `make gates` and `make ci-gates-parity` pass; engine version + CHANGELOG,
      annotated tag, fast-forward merge, push `main` + tag; no apply.

## Non-goals

- No composition pin, app tag, runtime pin or live host is changed here.
- No app code is copied into a writable directory; no second pointer or
  v2 consumer-link fallback is added.

## Evidence / Verify

Worktree `.worktrees/REQ-029/`, branch
`ticket/REQ-029-generations-v3-locality`. Commits: `3540516` (plan),
`d7c27ab` (implementation + release metadata), plus this evidence commit.
Annotated tag `v0.1.43` on the evidence commit; no apply was run.

- Locality/layout:
  - `ansible/roles/state_links/{vars,tasks}/main.yml` creates exactly four
    provisioning-owned stable links (`gtk-3.0`, `gtk-4.0`, `rofi`, `btop`) with
    `src: {{ state_links_state_current_palette_dir }}/{{ item.target }}` and
    `dest: {{ state_links_spine_config_dir }}/{{ item.spine }}`; there is no
    `config/ags` or `appearance` entry.
  - `ansible/playbooks/config-links-post-seed.yaml` roles:
    `[config_links, state_links]`.
  - `ansible/roles/wlogout_config/vars/main.yml`:
    `wlogout_config_state_palette_file = .../dotfiles/current/palette/colors.gtk.css`;
    `tasks/main.yml` sets `COLORS_FILE_PATH` to that var and carries no
    `config/ags/colors.css`.
  - `ansible/playbooks/runtime-seed.yaml` now checks
    `runtime_seed_generation_manifest = .../dotfiles/current/manifest.json`,
    asserts `version == 3`, a 64-hex `generationHash`, and
    `current` target basename == manifest hash; the v2 `current.json` /
    consumer-link list is gone.
  - `ansible/roles/ags_apps_units/vars/main.yml` adds
    `ags_apps_units_forbidden_runtime_artifacts` (`appearance.css`, `skin.css`,
    `skin.json`, `tokens.json`, `colors.css`, `colors.*`); `_one.yml` sweeps
    them from an existing tag and asserts `find` reports zero. `_verify_unit`
    and `_verify_runtime` use the v3 `appearance-refresh` + `genHash` ack.
  - `ansible/roles/verify/vars/main.yml` adds
    `verify_state_generation_manifest`, `verify_state_current_palette_dir`,
    `verify_generation_contract_tag: v0.8.0`,
    `verify_generation_manifest_version: 3`, the stable-link list (gtk/rofi/
    btop only) and `verify_app_tag_forbidden_runtime_artifacts`.
  - `ansible/roles/verify/tasks/main.yml` stats the generation manifest,
    validates `generationHash`/current basename/mode/skin/intent,
    `appearance/tokens.json` and every `appearance/<configDir>.css` target when
    present; checks stable links equal
    `current/palette/<target>` and resolve; fails on runtime artifacts in app
    tags and on state symlinks into app tags. Absent generation state is
    tolerated (all generation tasks are gated on the manifest existing).
- Contracts: fixture tuple moves to `contracts: v0.8.0`; vendored
  `tests/fixtures/contracts/v0.8.0/` carries `PIN` plus the frozen
  `generation-manifest.schema.json` and
  `appearance-refresh-result.schema.json`.
- Tests: `tests/unit/test_v3_locality.py` (stable links, absent tolerance,
  generation-manifest verify, immutability, vendored contracts);
  `test_ags_apps_units_role.py` adds the reinstall sweep test and removes the
  in-tag palette-pointer fixture; `test_verify_role.py` builds a v3 generation
  fixture; `test_runtime_seed_playbook.py` asserts generation postconditions.

Commands:

- `make gates` → **rc=0**
  - `test`: `996 passed, 3 skipped, 55 deselected in 953.97s`
  - `lint`: `All checks passed!`
  - `hermetic`: `965 passed, 34 skipped, 55 deselected in 897.09s`
  - `lock-check`: `Resolved 33 packages in 0.65ms`
  - `docs-check`: rc=0 (silent)
- `make ci-gates-parity` → **rc=0**:
  `PASS gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test'];
  exempt=['assets-parity', 'ci-gates-parity', 'release']`.
- No `apply`/`bootstrap` was run against a host.
