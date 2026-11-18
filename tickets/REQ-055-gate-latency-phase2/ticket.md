---
id: REQ-055
title: "Add release preflight and CI test sharding/slow-test support"
kind: requirement
status: proposed
lane: direct
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-055/
branch: ticket/REQ-055-gate-latency-phase2
---

# Release preflight + CI sharding

## Requirement

Keep full release verification authoritative while removing avoidable release
latency and last-minute tag churn.

This is phase 2 after REQ-054 (`make dev` / changed-file gate). REQ-054 already
provides scoped development feedback; this ticket addresses release execution and
CI wall time.

## Triage evidence

- Engine release on 2026-11-18 required `v0.1.85` → `v0.1.88` because
  release-specific checks failed after tag creation (ExecStart quoting, expac
  chronology fixture).
- `make test`: 1077 passed in 55 minutes; `make hermetic`: 1042 passed in 46
  minutes.
- CI currently has one `test` job and one `hermetic` job; each runs the full
  suite serially.
- No release preflight target validates version/tag/CHANGELOG/pin/CI parity
  before tagging.

## Part A — release preflight

Add `scripts/release_preflight.py` and `make release-preflight`.

It must be a fast, read-only check (no tag creation, no build by default) and
fail closed. Validate:

- clean worktree and expected release branch (`main` unless overridden);
- package version in `pyproject.toml` (and `src/provisioning/__init__.py` if it
  carries a release version) is consistent;
- intended tag is supplied or derived deterministically, and does not already
  exist locally or on `origin`;
- `CHANGELOG.md` contains the version being released;
- `uv lock --check`;
- `make pin-audit`;
- `make ci-gates-parity`;
- `make docs-check`;
- release-sensitive fixture/verify preflight where cheap: use targeted tests
  rather than the full suite;
- clear pass/fail output naming the failed check.

Add tests for: version mismatch, missing changelog entry, existing local/remote
tag, dirty worktree, branch mismatch, and success. Do not create tags in tests.

## Part B — CI test sharding and slow support

Add deterministic sharding without changing test semantics:

- `scripts/pytest_shard.py --shard I/N` selecting test files by a stable sorted
  hash/order; every file assigned exactly once, no overlap, no omissions.
- `make test-shard SHARD=I/N`.
- CI `test` job becomes a matrix of 4 shards running `make test-shard`; keep the
  job name `test` so `ci-gates-parity` stays valid.
- Keep `make test` as the local full fast suite.
- Register a `slow` pytest marker and add `make test-fast` that excludes
  `slow`/integration/container_target for optional local use. Mark only
  demonstrably slow modules; do not mark the whole suite. The authoritative CI
  and release gates must still run all non-integration tests.
- Tests for shard coverage/no-overlap and the marker configuration.

## Non-goals

- No weakening of `make gates` or release coverage.
- No release tag in this ticket.
- No changes to test assertions or production behavior.
- No automatic tag creation.

## Acceptance

- [ ] `make release-preflight TAG=vX.Y.Z` catches version/tag/changelog/pin/CI
  parity/docs/lock failures with actionable messages.
- [ ] Preflight is read-only and does not create tags or apply changes.
- [ ] CI `test` runs 4 deterministic shards covering every test file exactly
  once; `ci-gates-parity` still passes.
- [ ] `make test` remains the full fast suite; `make test-fast` excludes
  registered slow tests.
- [ ] New tests and lint/docs/CI parity pass.
- [ ] Ticket records evidence and is merged to `main` without a release tag
  unless the repo flow requires one; the next release carries it.

## Implementation notes

- Keep `GATES` unchanged unless a new gate is genuinely added; if so, update
  `.github/workflows/gates.yml` and `ci-gates-parity` in the same commit.
- Avoid running the full suite locally for implementation; use targeted tests
  and dry-runs. Full coverage is validated by CI.
