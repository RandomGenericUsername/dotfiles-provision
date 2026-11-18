---
id: REQ-056
title: "Shard the hermetic CI gate"
kind: requirement
status: done
lane: direct
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-056/
branch: ticket/REQ-056-hermetic-sharding
---

# Shard the hermetic CI gate

## Requirement

REQ-055 sharded the `test` CI job into four deterministic shards, but the
`hermetic` job still runs the entire fast suite serially. On 2026-11-18 that
single job took 46 minutes. Shard it with the same deterministic file selection
while preserving the full hermetic coverage.

## Work

1. Add `make hermetic-shard SHARD=I/N` using `scripts/pytest_shard.py --fast`.
   It must run the same empty-HOME/XDG environment and foreign-cwd isolation as
   `make hermetic`, but only for the selected files.
2. Keep `make hermetic` as the full local hermetic gate.
3. Change the CI `hermetic` job to a 4-shard matrix running
   `make hermetic-shard SHARD=${{ matrix.shard }}/4`; keep the job name
   `hermetic` so `ci-gates-parity` remains valid.
4. Do not change `GATES`, test semantics, or the fast-suite membership.
5. Add/extend tests if the Makefile/workflow shape is already covered; at
   minimum prove the shard target is dry-run valid and parity passes.

## Acceptance

- [x] `make -n hermetic-shard SHARD=1/4` shows the hermetic env plus selected
  files.
- [x] CI hermetic job is a 4-shard matrix; every fast test file is covered
  exactly once across the shards.
- [x] `make hermetic` remains the full local gate.
- [x] `make ci-gates-parity` passes.
- [x] No release tag required; the next release carries it.

## Evidence

- `make -n hermetic-shard SHARD=1/4` → empty HOME/XDG + foreign cwd + selected
  absolute test files.
- `make hermetic-shard SHARD=1/4` → `200 passed, 16 skipped in 8.13s`.
- Workflow YAML parse: `test` matrix `{shard: [1,2,3,4]}` and `hermetic`
  matrix `{shard: [1,2,3,4]}`; job names unchanged.
- `make ci-gates-parity` → PASS; `GATES` unchanged.
- Shard selection uses the same deterministic `scripts/pytest_shard.py --fast`
  partition validated by REQ-055.
- No release tag created; the next engine release carries it.
