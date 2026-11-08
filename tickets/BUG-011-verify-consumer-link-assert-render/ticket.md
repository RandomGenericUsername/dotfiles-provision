---
id: BUG-011
title: "Verify fails finalizing the stable consumer-link assert: registered result dict used as the link item"
kind: bug
status: done
lane: 2
severity: high
links:
  openspec: none
  bmad: none
worktree: .worktrees/BUG-011/
branch: ticket/BUG-011-verify-consumer-link-assert-render
repro: "Run the verify role (or the live apply+verify) on a host that reaches 'Assert each stable palette consumer link names current/palette and resolves' with the passing v3 topology: ansible-playbook ansible/playbooks/verify.yaml -e install_dir=<install> -e manifests_dir=<manifests>."
observed: "[ERROR]: Task failed: Finalization of task args for 'ansible.builtin.assert' failed: Error while resolving value for 'fail_msg': object of type 'dict' has no attribute 'path'. Origin: .../roles/verify/tasks/main.yml:2237. The assert loop zips two registered task-result lists, but the fail_msg/that reference pair.1.path and pair.1.target instead of pair.1.item.path / pair.1.item.target; Ansible finalizes fail_msg eagerly even when the assertion passes, so every host reaching this task fails."
expected: "The assert renders cleanly on the passing topology. A wrong/missing stable link produces a normal assertion failure whose message names the link path (e.g. config/rofi/colors.rasi) and never a templating/'object of type dict' error. No other verify/state_links task applies an item attribute to a registered result dict instead of its item/stat."
---

# BUG-011 — verify consumer-link assert misuses the registered result dict

## Root cause

`verify/tasks/main.yml` registers two looped `stat` results and zips them:

```yaml
loop: >-
  {{ verify_consumer_symlink_checks.results
     | zip(verify_consumer_symlink_resolve_checks.results) | list }}
loop_control:
  loop_var: pair
```

Each `pair.N` is a full task-result dict (`item`, `stat`, `changed`, ...),
not the loop item. The assert body and `fail_msg` read `pair.1.path` and
`pair.1.target`, which do not exist on a result dict. Ansible renders
`fail_msg` eagerly during argument finalization, so the task fails before the
condition can pass — breaking verify and the live apply on every host.

## Repro

```bash
ansible-playbook ansible/playbooks/verify.yaml \
  -e install_dir=<install> -e manifests_dir=<manifests>
```

Observed on the v0.1.46 live apply+verify:

```
[ERROR]: Task failed: Finalization of task args for 'ansible.builtin.assert' failed:
Error while resolving value for 'fail_msg': object of type 'dict' has no attribute 'path'
Origin: .../roles/verify/tasks/main.yml:2237
```

## Expected

- The failing references become `pair.1.item.path` / `pair.1.item.target`
  (both zipped items name the same link); the message content is unchanged.
- The same audit covers the verify/state_links roles added for v3: no `.path`
  or other item attribute is read from a registered result dict instead of
  its `item` or `stat`.
- Regression tests run the real role/playbook so Ansible finalizes the assert
  args: the passing topology renders cleanly, and a wrong/missing link fails
  with the link path in the clean assertion message and no templating error.

## Acceptance

- [x] `fail_msg` and `that` reference `pair.1.item.path` /
      `pair.1.item.target`; message content is unchanged.
- [x] Verify/state_links (and v3-adjacent roles) audited for the same
      result-dict attribute mistake; every finding fixed without changing
      semantics.
- [x] A real `ansible-playbook` regression test renders the assert on the
      passing topology and forces the failure path for a wrong/missing link;
      the failure names the link path with no `object of type 'dict'` error.
- [x] `make gates`, `make ci-gates-parity` and the targeted verify/state-links
      tests pass (exact results recorded).
- [x] Engine `0.1.47` + CHANGELOG, annotated tag `v0.1.47` after the
      fast-forward merge; push `main` and the tag; GitHub Release carries only
      the 0.1.47 sdist and wheel.

## Audit

Every looped use of a registered `.results` list in `verify`, `state_links`,
`config_links`, `config_copies`, `ags_apps_units`, `assets`, `cli_tools`,
`compositor_configs` and `power_options` was checked for attributes read off
the result dict instead of its `item` / `stat`. The consumer-link pair was the
only instance of this class; `item.msg`, `item.content`, `item.source`,
`item.item.*`, `item.stat.*` and the flattened `find` file dicts are correct.

The same run surfaced two latent failures masked by the finalization error,
fixed without changing intent:

- The v3 generation-target condition used `appearance/\1.css` in a bare
  conditional. Ansible's conditional parser treats `\1` as an escape, so the
  expected list became literal control-character targets; the condition is now
  `appearance/\\1.css` (one backreference at substitution time). Evidence:
  a focused `assert` with the old form fails while the new form passes
  (`/tmp/bug011fix/probe5.yml`, probe6).
- `test_verify_passes_on_a_provisioned_machine`'s negative lock deleted
  `current/colors.conf`, which v3 verify no longer reads; it now removes
  `current/palette/colors.conf`, the file the palette gate actually asserts.

## Evidence

Implementation commit: `09ab230` (`fix(BUG-011): render the stable
consumer-link assert; release 0.1.47`).

Pre-fix reproduction (`uv run pytest -q
tests/unit/test_verify_role.py::TestVerifyRuntime::test_verify_passes_on_a_provisioned_machine`)
→ exit 1 after 80.25s with:

```
TASK [verify : Assert each stable palette consumer link names current/palette and resolves]
[ERROR]: Task failed: Finalization of task args for 'ansible.builtin.assert' failed:
Error while resolving value for 'fail_msg': object of type 'dict' has no attribute 'path'
failed=1
```

After the fix, the same full playbook run is green (`failed=0`, `ok=327`).

- `make gates` → exit 0 (`/tmp/opencode/bug011-gates.log`):
  - `test`: **1005 passed, 3 skipped, 60 deselected** in 1160.67s
  - `lint`: **All checks passed**
  - `hermetic`: **974 passed, 34 skipped, 60 deselected** in 1088.94s
  - `lock-check`: **Resolved 33 packages**
  - `docs-check`: exit 0 (silent; no missing docs/symlink)
- `make ci-gates-parity` →
  `PASS gates=['docs-check', 'hermetic', 'lint', 'lock-check', 'test'] jobs=['assets-parity', 'ci-gates-parity', 'docs-check', 'hermetic', 'lint', 'lock-check', 'release', 'test'] exempt=['assets-parity', 'ci-gates-parity', 'release']`.
- Targeted verify/state-links tests
  (`TestVerifyConsumerLinkRender`, `TestVerifyConsumerLinks`,
  `TestVerifyRuntime::test_verify_passes_on_a_provisioned_machine`,
  `TestVerifyRuntime::test_verify_fails_when_a_rofi_palette_link_is_missing`,
  `test_v3_locality.py`) → **22 passed** in 291.20s
  (`/tmp/opencode/bug011-targeted.log`). This includes:
  - passing topology: the assert task renders `All assertions passed`, no
    `Finalization of task args` / `object of type 'dict'`;
  - wrong target and missing link: normal assertion failure naming
    `config/rofi/colors.rasi` and `is not the provisioning-owned stable link`,
    with no templating error.
- Release: engine `0.1.47`, annotated tag `v0.1.47` on the fast-forwarded
  `main`; `main` and tag pushed; GitHub Release carries only the 0.1.47 sdist
  and wheel. No `apply` was run in this ticket.

## Non-goals

- No live apply is run here.
- No composition, runtime, assets or app tag is changed.
