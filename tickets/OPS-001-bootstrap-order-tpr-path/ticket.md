---
id: OPS-001
title: "Fix bootstrap order and the tpr checkout path"
kind: ops-task
status: done
lane: direct
links:
  openspec: none
  bmad: none
worktree: none
branch: main
---

# Fix bootstrap order and the tpr checkout path

## Work

- Import `compositor-configs.yaml` before `ags-apps-units.yaml` so the app role
  reconciles autostart against the current assets-owned
  `<install>/config/hypr/autostart.lua` instead of the previous pin's copy.
  `gui-tools` still precedes the installer so dunst is masked first.
- Point `assets_tpr_templates_source` and the `verify_tpr_*` checkout/pin at
  `<install>/cli-tools/tpr/<tag>`, the path `cli_tools` installs via its
  `{name, repo, tag}` checkout shape. The deployed config dir stays
  `config/theme-producer`; tpr remains installed as the opt-in producer.

## Done-when

`make gates` is green and the engine is tagged `v0.1.24`.

## Evidence

- `ansible/playbooks/bootstrap.yaml` imports compositor-configs before
  ags-apps-units; `tests/unit/test_bootstrap_playbook.py` and
  `tests/unit/test_ags_apps_units_role.py` lock the order.
- `ansible/roles/{assets,verify}/vars/main.yml` read `cli-tools/tpr/...`;
  `test_assets_role.py`, `test_template_vars_parity.py` and
  `test_verify_role.py` lock the path.
- Targeted suites + `tests/integration/test_ansible_dryrun.py`, `make lint`,
  `make lock-check`, `make docs-check`: pass.
