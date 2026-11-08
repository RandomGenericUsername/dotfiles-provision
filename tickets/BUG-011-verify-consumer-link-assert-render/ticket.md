---
id: BUG-011
title: "Verify fails finalizing the stable consumer-link assert: registered result dict used as the link item"
kind: bug
status: in-progress
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

- [ ] `fail_msg` and `that` reference `pair.1.item.path` /
      `pair.1.item.target`; message content is unchanged.
- [ ] Verify/state_links (and v3-adjacent roles) audited for the same
      result-dict attribute mistake; every finding fixed without changing
      semantics.
- [ ] A real `ansible-playbook` regression test renders the assert on the
      passing topology and forces the failure path for a wrong/missing link;
      the failure names the link path with no `object of type 'dict'` error.
- [ ] `make gates`, `make ci-gates-parity` and the targeted verify/state-links
      tests pass (exact results recorded).
- [ ] Engine `0.1.47` + CHANGELOG, annotated tag `v0.1.47` after the
      fast-forward merge; push `main` and the tag; GitHub Release carries only
      the 0.1.47 sdist and wheel.

## Evidence

Implementation commit: TBD.

- `make gates` → TBD.
- `make ci-gates-parity` → TBD.
- Targeted tests → TBD.
- Release verification (`git ls-remote`, `gh release view`) → TBD.

## Non-goals

- No live apply is run here.
- No composition, runtime, assets or app tag is changed.
