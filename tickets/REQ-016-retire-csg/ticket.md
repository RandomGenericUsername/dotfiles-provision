---
id: REQ-016
title: "Retire CSG from provisioning (tpr is the sole palette producer)"
kind: requirement
status: in-progress
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

- [ ] `settings`: csg settings template, `settings_csg_image_tag`, cache/config
      dirs and `settings_files` entry removed.
- [ ] `assets`: `csg-templates` source/copy, native-checkout dir assertion and
      config-in-spine relocation removed.
- [ ] `verify`: `verify_csg_version`, `verify_csg_contract_version`,
      checkout/pin/image/contract tasks and result keys removed.
- [ ] `filesystem`, `config_links`, `cli_tools`, `runtime_daemon`,
      `group_vars/**` carry no csg behavior; `runtime_palette_producer`
      defaults to `tpr` and the domain assert accepts only `tpr`.
- [ ] Composition fixtures (`cli-tools`, `assets`, `packages`, `filesystem`)
      carry no csg entries.
- [ ] Tests that asserted csg behavior are removed or rewritten; the pin-parity
      set no longer includes csg.
- [ ] `rg -ni 'csg|color-scheme-generator' ansible src tests/fixtures
      tests/unit tests/integration --glob '*.{yml,yaml,py,j2}'` returns only
      explicit historical comments.
- [ ] Version `0.1.30` + CHANGELOG entry. No tag/push/merge.

## Evidence / Verify

- Branch: `ticket/REQ-016-retire-csg`; worktree `.worktrees/REQ-016/`.
- Runtime contract: dotfiles-runtime >= v0.5.1 rejects `csg`; tpr is the sole
  producer.
- `rg` sweep: only three justified historical comments remain
  (`group_vars/all.yml`, `runtime_daemon/tasks/main.yml`).
- `make gates` and `make ci-gates-parity` results recorded in the Outcome
  section below (orchestrator run).

## Outcome

In progress. No tag, push or merge.
