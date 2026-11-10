---
id: BUG-012
title: "Verify rejects the assets v0.15.0 skins envelope because it still expects contracts v0.7.0"
kind: bug
status: in-progress
lane: 2
severity: high
links:
  openspec: none
  bmad: none
worktree: .worktrees/BUG-012/
branch: ticket/BUG-012-v0150-skins-contract-tag
repro: "On a host provisioned with assets v0.15.0/runtime v1.1.0, run: dotfiles-provision verify (or ansible-playbook ansible/playbooks/verify.yaml -e install_dir=<install> -e manifests_dir=<manifests>)."
observed: "verify fails at 'Assert the deployed skins schema envelope is the v2 appearance envelope': /home/inumaki/.local/share/dotfiles/skins/schema.json is not the pinned Appearance v2 envelope: expected schema_major 2, canonical tag v0.7.0, the three vendored delegates (manifest/json/artifact), the five token groups ... and the resolved tokens.json contract. The assets v0.15.0 skins envelope names canonical.tag v0.9.0 and vendors generation-manifest.schema.json, while verify_skins_expected_contract_tag is still v0.7.0 and verify_skins_contract_files omits the generation schema."
expected: "verify accepts the released assets v0.15.0 skins envelope: schema_major 2, canonical.tag v0.9.0, vendored manifest/json/artifact delegates plus the vendored generation-manifest schema, the five token groups and the resolved appearance-json tokens.json contract. A v0.7.0 or otherwise wrong/missing canonical tag fails with a clean assertion naming the expected v0.9.0 tag; the genuine contracts v0.9.0 host-bearing generation fixture still passes."
---

# BUG-012 — verify expects the stale skins contracts tag after assets v0.15.0

## Root cause

`ansible/roles/verify/vars/main.yml` still pins
`verify_skins_expected_contract_tag: v0.7.0`. Assets v0.15.0 re-vendored the
skins contracts at **v0.9.0** and its `skins/schema.json` now declares
`canonical.tag: v0.9.0`, adds `generation-manifest.schema.json` to
`canonical.paths` / `canonical.vendored_paths`, and ships that schema in
`skins/contracts/` with a PIN sha256 line. Verify therefore rejects a correctly
deployed v0.15.0 corpus. It also omitted the generation schema from
`verify_skins_contract_files`, so the PIN hash assertion never checked that
released vendored file.

## Repro

```bash
dotfiles-provision verify
# or
ansible-playbook ansible/playbooks/verify.yaml \
  -e install_dir=<install> -e manifests_dir=<manifests>
```

Observed on the live assets v0.15.0 / runtime v1.1.0 host:

```
verify : Assert the deployed skins schema envelope is the v2 appearance envelope
/home/inumaki/.local/share/dotfiles/skins/schema.json is not the pinned
Appearance v2 envelope: expected schema_major 2, canonical tag v0.7.0 ...
```

## Expected

- `verify_skins_expected_contract_tag` is **v0.9.0**, matching the released
  assets v0.15.0 `skins/schema.json` and `skins/contracts/PIN`.
- The envelope assertion keeps every existing check and explicitly accepts the
  released shape: the three `canonical.delegates` keys (manifest/json/artifact)
  plus the fourth canonical vendored schema, `generation-manifest.schema.json`,
  in `canonical.vendored_paths`.
- `verify_skins_contract_files` includes `generation-manifest.schema.json`, so
  the PIN sha256 assertion covers all seven released vendored contracts.
- Regression tests prove the v0.9.0/v0.15.0 fixture passes; v0.7.0 and v0.14.0
  canonical-tag expectations are rejected; a missing/wrong canonical tag fails;
  and the existing contracts v0.9.0 host-bearing generation fixture remains
  accepted.

## Acceptance

- [x] `verify_skins_expected_contract_tag` is **v0.9.0**; every related
      skins/appearance schema-envelope mirror under `ansible/roles/verify`
      agrees.
- [x] The deployed envelope assertion accepts the released assets v0.15.0
      shape and includes `generation-manifest.schema.json` in the hash-checked
      contract set, without weakening schema_major, canonical tag, delegates,
      token groups or resolved `tokens.json` checks.
- [x] Tests cover the v0.15.0/v0.9.0 positive fixture, reject stale v0.7.0 /
      v0.14.0 canonical tags, reject a missing/wrong canonical tag, and keep the
      contracts v0.9.0 host-bearing generation fixture green.
- [x] v0.1.51's contracts v0.9.0 / assets v0.15.0 mirrors and all v3 behavior
      are preserved.
- [x] Targeted verify/assets/skins tests, `make gates` and
      `make ci-gates-parity` pass; engine `0.1.52`; annotated tag `v0.1.52`;
      GitHub Release carries only the 0.1.52 sdist/wheel; no apply.

## Evidence

Implementation commit `7bced357`; planning commit `0bef479`.

Exact changes:

- `ansible/roles/verify/vars/main.yml`:
  `verify_skins_expected_contract_tag: v0.7.0` → **`v0.9.0`**;
  `verify_skins_contract_files` gains
  `generation-manifest.schema.json` (seven names → eight including `PIN`).
- `ansible/roles/verify/tasks/main.yml`: the envelope assertion keeps
  `schema_major == 2`, the `v0.9.0` canonical tag, the exact
  `artifact/json/manifest` delegate keys, the five token groups and the
  `appearance-json.schema.json` resolved-document path, and adds an explicit
  check that `canonical.vendored_paths` contains all four canonical schemas:
  `appearance-manifest`, `appearance-json`, `appearance-artifact` and
  `generation-manifest`. No check was relaxed.
- `ansible/roles/assets/tasks/main.yml`: stale comment corrected to
  `schema_major 2` / assets v0.15.0 (no behavior change).
- `tests/unit/test_verify_role.py`: the deployed fixture now models the real
  v0.15.0 `skins/schema.json` (`canonical.tag v0.9.0`, seven canonical paths,
  vendored generation schema) and the PIN (`contracts=v0.9.0`); adds positive
  v0.15.0/v0.9.0, stale v0.7.0/v0.14.0, missing canonical tag, missing
  generation path and missing generation contract cases.
- `pyproject.toml`/`uv.lock` `0.1.51` → `0.1.52`, plus the `CHANGELOG.md`
  0.1.52 entry.

Audit against the deployed assets v0.15.0 `skins/schema.json` (read-only):
schema_major `2`; canonical.tag `v0.9.0`; `canonical.vendored` `true`;
delegates exactly `artifact`/`json`/`manifest`; `generation-manifest.schema.json`
present in `canonical.paths` and `canonical.vendored_paths` (the released
envelope keeps generation as a vendored canonical schema, not a fourth
delegates key); five `frozen.token_groups`; resolved document
`skins/contracts/appearance-json.schema.json`; PIN `contracts=v0.9.0` with
seven sha256 lines. A direct Ansible probe of those exact conditions against
`/home/inumaki/.local/share/dotfiles/assets/v0.15.0/skins/schema.json` →
`All assertions passed`, `failed=0`.

Gates and tests:

- Targeted `TestVerifySkinPlane` + assets schema contract +
  `test_skins_pin_is_v0150...` → **25 passed** (380.31s).
- Targeted new envelope cases → **6 passed** (153.68s).
- `TestVerifyRuntime::test_verify_accepts_a_host_bearing_generation` (contracts
  v0.9.0 host-bearing generation fixture) → **1 passed** (276.64s).
- `make gates` → **rc 0** (`/tmp/opencode/bug012-gates.log`):
  - `test`: **1017 passed, 3 skipped, 67 deselected** in 2333.40s
  - `lint`: **All checks passed**
  - `hermetic`: **984 passed, 36 skipped, 67 deselected** in 2200.61s
  - `lock-check`: **Resolved 33 packages**
  - `docs-check`: rc 0 (silent; no missing docs/symlink)
- `make ci-gates-parity` →
  `PASS gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test'] jobs=[...]`.
- `make build` → rc 0; built `dotfiles_provision-0.1.52.tar.gz` and
  `dotfiles_provision-0.1.52-py3-none-any.whl`; wheel content check PASS.

Release: engine `0.1.52`, annotated tag `v0.1.52` on the fast-forward merge
commit, GitHub Release carries only the 0.1.52 sdist and wheel. No apply and no
live-host or composition edit. Composition can install installer v0.1.52 and
then apply/verify against the already pinned contracts v0.9.0 / assets v0.15.0 /
runtime v1.1.0 tuple.

## Non-goals

- No apply and no live-host edit.
- No composition, runtime, app, contract-schema or downstream consumer edit.
- No change to app tags, state links or wlogout behavior.
