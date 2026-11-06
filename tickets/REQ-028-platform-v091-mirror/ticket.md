---
id: REQ-028
title: "Mirror ags-platform v0.9.1 in the engine pins"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-028/
branch: ticket/REQ-028-platform-v091-mirror
---

# Mirror ags-platform v0.9.1 in the engine pins

## Requirement

The `dotfiles-v3` composition tuple now pins `ags-platform: v0.9.1` (palette
mode metadata, required by theme-producer v0.6.0 output), but the engine still
installs and verifies `v0.9.0`. `make deploy-coverage` fails before
provisioning:

`ansible/roles/ags_platform/vars/main.yml ags_platform_version = 'v0.9.0' does not resolve 'v0.9.1'`

Every platform pin mirror — the role, the verify mirror, the composition
fixture and the tests that stand in for a host — must move to `v0.9.1`. The
unit dir, pin file and shared shortcut stay derived from the one version var.
`contracts: v0.7.0` and `dotfiles-assets: v0.13.0` are unchanged, and
`dotfiles-v3` is not edited here.

## Acceptance

- [x] `ansible/roles/ags_platform/vars/main.yml`: `ags_platform_version` is
      `v0.9.1`; the unit dir, pin file and shared shortcut still derive from
      that one var.
- [x] `ansible/roles/verify/vars/main.yml`: `verify_ags_platform_version` is
      `v0.9.1`; unit dir/pin/shortcut remain derived, with no stale literal.
- [x] Composition fixture `program-tuple.yaml`: `ags-platform: v0.9.1`,
      `contracts: v0.7.0`, `dotfiles-assets: v0.13.0`.
- [x] Unit tests that stand in for a host (`test_ags_platform_role.py`,
      `test_ags_apps_units_role.py`, `test_verify_role.py`) use `v0.9.1`; no
      hardcoded `v0.9.0` fixture/simulation literal remains.
- [x] Targeted AGS/verify tests, `make gates` and `make ci-gates-parity` pass;
      a temporary `dotfiles-v3` copy with `installer.pin: v0.1.42` passes
      `make deploy-coverage` while its program tuple names `v0.9.1`.
- [x] Engine `0.1.42` + CHANGELOG, annotated tag `v0.1.42` after the
      fast-forward merge; push `main` and the tag; no apply.

## Evidence / Verify

Worktree `.worktrees/REQ-028/`, branch
`ticket/REQ-028-platform-v091-mirror`. Commits: `27fc21d` (plan),
`4aeda9f` (implementation + release metadata), plus this evidence commit.
Annotated tag `v0.1.42` created on the fast-forward merge commit.

- Upstream tag exists: `git -C ../ags-platform tag --sort=-v:refname | head -1`
  → `v0.9.1`.
- Pin mirrors:
  `rg -n 'ags_platform_version:|verify_ags_platform_version:|ags-platform:'
  ansible/roles/ags_platform/vars/main.yml ansible/roles/verify/vars/main.yml
  tests/fixtures/composition/dotfiles/provisioning/program-tuple.yaml`
  → role `v0.9.1`, verify `v0.9.1`, fixture tuple `ags-platform: v0.9.1`.
  The unit dir is `{{ ags_platform_install_root }}/{{ ags_platform_version }}`,
  the pin file is `<install>/ags-platform/pinned`, and the shared shortcut is
  owned by `ags_apps_units`; no path literal changed.
- Stale-literal sweep:
  `rg -n 'v0\.9\.0' --glob '!CHANGELOG.md' --glob '!tickets/**' .`
  → no matches (historical CHANGELOG/ticket records are untouched).
- Targeted AGS/verify suites:
  `uv run --frozen pytest -q tests/unit/test_ags_platform_role.py
  tests/unit/test_ags_apps_units_role.py tests/unit/test_verify_role.py
  -m "not integration and not container_target"` → **179 passed,
  15 deselected in 543.31s**.
- `make gates` → **rc=0**:
  - `test`: `952 passed, 31 skipped, 55 deselected in 737.19s`
  - `lint`: `All checks passed!`
  - `hermetic`: `949 passed, 34 skipped, 55 deselected in 691.70s`
  - `lock-check`: `Resolved 33 packages in 0.70ms`
  - `docs-check`: rc=0
- `make ci-gates-parity` → **rc=0**:
  `PASS gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test']`;
  CI-only exempt `assets-parity, ci-gates-parity, release`.
- Composition proof without editing `dotfiles-v3` (temporary copy of its
  working tree, whose tuple already names `ags-platform: v0.9.1`; engine cache
  pre-populated, offline):
  - Red with `installer.pin: v0.1.41` (engine `v0.9.0`):
    `cd /tmp/opencode/req028-dcv/red && DOTFILES_PROVISION_OFFLINE=1 make deploy-coverage`
    → **rc=2**:
    `FAIL: dotfiles/provisioning/program-tuple.yaml:
    ansible/roles/ags_platform/vars/main.yml ags_platform_version = 'v0.9.0'
    does not resolve 'v0.9.1'`.
  - Green with `installer.pin: v0.1.42` and this engine tree cached as
    `.dev/dotfiles-provision-v0.1.42`:
    `cd /tmp/opencode/req028-dcv/green && DOTFILES_PROVISION_OFFLINE=1 make deploy-coverage`
    → **rc=0**: `CHECK pinned installer engine v0.1.42 …` and
    `deploy-coverage: engine final topology — tuple ags-platform v0.9.1 +
    dotfiles-assets v0.13.0`.

## Handoff (dotfiles-v3)

- `dotfiles/provisioning/installer.pin`: `v0.1.42`
- `dotfiles/provisioning/program-tuple.yaml`: `ags-platform: v0.9.1`,
  `contracts: v0.7.0`, `dotfiles-assets: v0.13.0`

No `dotfiles-v3` file is edited by this ticket.
