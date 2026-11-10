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

- [ ] `verify_skins_expected_contract_tag` is **v0.9.0**; every related
      skins/appearance schema-envelope mirror under `ansible/roles/verify`
      agrees.
- [ ] The deployed envelope assertion accepts the released assets v0.15.0
      shape and includes `generation-manifest.schema.json` in the hash-checked
      contract set, without weakening schema_major, canonical tag, delegates,
      token groups or resolved `tokens.json` checks.
- [ ] Tests cover the v0.15.0/v0.9.0 positive fixture, reject stale v0.7.0 /
      v0.14.0 canonical tags, reject a missing/wrong canonical tag, and keep the
      contracts v0.9.0 host-bearing generation fixture green.
- [ ] v0.1.51's contracts v0.9.0 / assets v0.15.0 mirrors and all v3 behavior
      are preserved.
- [ ] Targeted verify/assets/skins tests, `make gates` and
      `make ci-gates-parity` pass; engine `0.1.52`; annotated tag `v0.1.52`;
      GitHub Release carries only the 0.1.52 sdist/wheel; no apply.

## Evidence

Recorded after the gates complete.

## Non-goals

- No apply and no live-host edit.
- No composition, runtime, app, contract-schema or downstream consumer edit.
- No change to app tags, state links or wlogout behavior.
