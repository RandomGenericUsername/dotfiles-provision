---
id: REQ-016
title: "Retire CSG from provisioning (tpr is the sole palette producer)"
kind: requirement
status: done
lane: 2
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-016/
branch: ticket/REQ-016-retire-csg
---

# Retire CSG from provisioning

## Requirement

The runtime rejects `csg` (runtime v0.5.1), and `tpr` is now the sole palette
producer. The remaining csg weight in the engine is dead: no bootstrap path
should install, render, link, verify or document it. The composition manifests
own tool lists, so the engine must keep working for any manifest that omits
csg.

## Acceptance

- [x] `settings`: csg settings template, `settings_csg_image_tag`, cache/config
      dirs and `settings_files` entry removed.
- [x] `assets`: `csg-templates` source/copy, native-checkout dir assertion and
      config-in-spine relocation removed.
- [x] `verify`: `verify_csg_version`, `verify_csg_contract_version`,
      checkout/pin/image/contract tasks and result keys removed.
- [x] `filesystem`, `config_links`, `cli_tools`, `runtime_daemon`,
      `group_vars/**` carry no csg behavior; `runtime_palette_producer`
      defaults to `tpr` and the domain assert accepts only `tpr`.
- [x] Composition fixtures (`cli-tools`, `assets`, `packages`, `filesystem`)
      carry no csg entries.
- [x] Tests that asserted csg behavior are removed or rewritten; the pin-parity
      set no longer includes csg.
- [x] `rg -ni 'csg|color-scheme-generator' ansible src tests/fixtures
      tests/unit tests/integration --glob '*.{yml,yaml,py,j2}'` returns only
      explicit historical comments.
- [x] Version `0.1.30` + CHANGELOG entry. No tag/push/merge.

## Evidence / Verify

- Branch: `ticket/REQ-016-retire-csg`; worktree `.worktrees/REQ-016/`.
- Runtime contract: dotfiles-runtime >= v0.5.1 rejects `csg`; tpr is the sole
  producer.
- `rg` sweep: only three justified historical comments remain
  (`group_vars/all.yml`, `runtime_daemon/tasks/main.yml`).
- `rg` result (exact):
  ```
  ansible/inventory/group_vars/all.yml:56:#   (REQ-010 / runtime REQ-004). REQ-016 retired csg: `tpr` is the sole
  ansible/inventory/group_vars/all.yml:57:#   producer (runtime >= v0.5.1 rejects csg). This is a PROVISIONING INPUT
  ansible/roles/runtime_daemon/tasks/main.yml:18:# rejects csg before it reads producer.json).
  ```
- `make gates` → **PASS** (rc=0): `945 passed, 3 skipped, 52 deselected`
  (fast suite, 22m22s); `ruff check src tests` → `All checks passed!`;
  hermetic `914 passed, 34 skipped, 52 deselected` (18m57s); `uv lock --check`
  → `Resolved 33 packages in 1ms`; `docs-check` clean.
- `make ci-gates-parity` → **PASS**: gates `docs-check, hermetic, lint,
  lock-check, test`; CI jobs include those + `assets-parity`,
  `ci-gates-parity`, `release` (both exempt where declared).
- Engine version `0.1.30`; `uv.lock` re-locked to `0.1.30`.
- Code commit `ac7d22d` (tag `v0.1.30`); this ticket-evidence commit rides on
  top of it on `ticket/REQ-016-retire-csg`.

## Outcome

CSG is retired from provisioning. `tpr` is the sole palette producer
(`runtime_palette_producer` defaults to `tpr`; `runtime_daemon` accepts only
`tpr`). No bootstrap path installs, renders, links, verifies or documents csg;
the engine still reads all tool lists from the composition manifests, so a
manifest without csg is the supported shape.

No tag, push or merge.

## Outcome

Released engine `v0.1.30` (tag pushed) and deployed with PIN-0122 on 2026-10-31
(bootstrap verify green, 291 tasks; no csg gates/paths remain):
- provisioning no longer installs, renders, links or verifies csg; engine
  defaults `runtime_palette_producer` to `tpr` and asserts tpr-only;
- host leftovers removed: `~/.local/bin/csg`, the uv tool
  `color-scheme-generator`, `cli-tools/csg/*` checkouts, the
  `color-scheme-generator` config link + spine dir, and all `csg-*` images;
- live state: producer `tpr/native/container`, palette `palette.v1` conforming,
  icons still role-based (`primary` `#b9c3ff`, `on_backdrop` `#e3e1e9`),
  `doctor` clean; `rg -ni 'csg' ansible src` → comments only.
