---
id: BUG-008
title: "runtime-seed ignores the configured palette producer (single/double underscore mismatch)"
kind: bug
status: done
lane: 2
severity: high
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-013/
branch: ticket/REQ-013-bootstrap-producer-and-rofi
repro: "Export RUNTIME_PALETTE_PRODUCER=tpr and run the bootstrap/runtime-seed stage. The runtime reads RUNTIME__PALETTE__PRODUCER, so the seed silently uses the default csg."
observed: "2026-10-29 bootstrap started 17:10:44 with RUNTIME_PALETTE_PRODUCER=tpr; runtime-seed produced the CSG palette bf8d7524… at 22:18:35Z, while the first tpr palette 01c9360b… appears only after the manual tpr-native install and manual set at 22:32:46Z. The daemon/environment.d got tpr, but the seed command did not."
expected: "The bootstrap seed and every runtime composition resolve the same configured producer; selecting tpr must produce a tpr cache entry during bootstrap, not csg."
---

# BUG-008 — runtime-seed ignores the configured palette producer

## Root cause

Provisioning uses `RUNTIME_PALETTE_PRODUCER` (single underscore) as its input
and writes `environment.d`/the daemon unit with
`RUNTIME__PALETTE__PRODUCER` (double underscore). `runtime-seed.yaml` has no
`environment:` block, so the seed child inherits the single-underscore variable,
which `dotfiles-runtime` never reads. The runtime defaults to `csg`. The
group_vars comment claiming “ONE var change flips it for BOTH consumers”
(`ansible/inventory/group_vars/all.yml:55-68`) is false for runtime-seed.

## Proper fix

Do not paper over this with another env injection. Make the producer a
runtime-owned config file read by every composition root:

```text
<install_spine>/config/dotfiles-runtime/producer.json
{"schema_version":1,"producer":"tpr","tpr_engine":"native","tpr_runtime":"container"}
```

- `dotfiles-runtime` REQ-004 implements the reader, resolution order and
  `inspect producer`; ambient env is non-authoritative.
- `dotfiles-provision` renders the file in `runtime_daemon` before the daemon
  starts and before `runtime-seed`; adds `config/dotfiles-runtime` to the
  filesystem spine; removes env.d/unit producer authority in the same change.
- `runtime-seed` needs no producer env; the runtime reads the spine config.
- `verify` asserts the config exists and its producer/engine match the selected
  provisioning values.

## Acceptance

- [ ] A bootstrap with `runtime_palette_producer=tpr` produces a tpr palette
  during runtime-seed; no manual set is needed.
- [ ] The seed and daemon resolve the same producer/config.
- [ ] No `RUNTIME__PALETTE__PRODUCER` env is required or authoritative; stale
  env is warned about by the runtime.
- [ ] Targeted provisioning tests and races cover the config render order,
  runtime-seed, and verify; release the engine tag after the runtime release.

## Cross-references

- `dotfiles-runtime` REQ-004 — producer config reader.
- `dotfiles-provision` BUG-007 — tpr container/verify/pin changes.
- `dotfiles-provision` BUG-006 — rofi pre/post-seed exposure.

## Closeout evidence (2026-10-30)

- Bootstrap produced the tpr producer config and a tpr palette (`01c9360b…`)
  during runtime-seed; the old single/double underscore env was not used.
- `inspect producer` with ambient `RUNTIME__PALETTE__PRODUCER=csg` reports the
  config as authoritative and the env as ignored.
- Seed/tests prove config-before-seed and no producer env injection.
