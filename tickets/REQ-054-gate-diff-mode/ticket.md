---
id: REQ-054
title: "Add a fail-closed diff/dev gate for changed-file feedback"
kind: requirement
status: proposed
lane: direct
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-054/
branch: ticket/REQ-054-gate-diff-mode
---

# Diff/dev gate for changed-file feedback

## Requirement

Reduce local feedback from the full engine suite to the tests actually affected
by the current diff, without weakening release verification.

The engine currently runs `test` and `hermetic` over the same 1,100+ test fast
suite for every release candidate. In the 2026-11-18 Lane B release, `make test`
took 55 minutes and `make hermetic` took 46 minutes. That is appropriate once
for a release, not for every edit while developing.

Add a **fail-closed** development gate:

```bash
make dev
make gates-diff BASE=origin/main
make gates-role ROLE=verify
```

`make gates` remains the release authority. `make dev` must never be treated as
proof that a release is safe.

## Triage evidence

- `Makefile`: `GATES := test lint hermetic lock-check docs-check`.
- `make test` and `make hermetic` both execute `pytest -q $(FAST)`; hermetic
  repeats the same suite under empty HOME/XDG.
- Measured 2026-11-18: test 1077 passed in 3300.87s; hermetic 1042 passed in
  2775.97s.
- 1,165 tests collected; 42 test files invoke Ansible/playbooks.
- There is no changed-file selector, no role-level target, no slow-test marker,
  and no diff-mode fallback.
- Release churn required four engine tags (`v0.1.85`–`v0.1.88`) and four
  composition tags because release-specific checks were discovered late.

## Design

### Command behavior

`make dev` computes the change set from:

- the merge-base with `BASE` (default `main` or `origin/main`; resolve
  explicitly and print the base), plus
- the working-tree and staged changes.

It then runs:

1. cheap global checks: `ruff check src tests`, `docs-check`, and `pin-audit`
   when manifests/fixtures are touched;
2. the mapped tests for every changed path;
3. a clear summary of which paths triggered which tests.

It does **not** run hermetic by default. Provide `make dev-hermetic` or a
`HERMETIC=1` option for an explicit local hermetic run.

### Mapping and fail-closed rules

Use an explicit mapping file, e.g. `scripts/gate-map.yaml`, plus deterministic
path rules:

- `ansible/roles/<role>/**` → the role's test file(s), plus any fixture/seam
  tests that assert that role.
- `ansible/inventory/group_vars/**` → `test_ansible_scaffold.py`,
  `test_packages_role.py`, and related mapping tests.
- `ansible/playbooks/**` → `test_bootstrap_playbook.py` and affected role tests.
- `tests/unit/<name>.py` → itself.
- `tests/fixtures/**` → scaffold, composition-seam, and fixture-sensitive tests.
- `scripts/pin-audit.py`, manifests, or pin fixtures → pin/scaffold tests.
- docs/tickets only → docs-check/INDEX validation.
- `Makefile`, `pyproject.toml`, `scripts/gate_diff.py`, or
  `scripts/gate-map.yaml` → full fast suite.
- unknown path → full fast suite, with a warning naming the path.

The gate must fail closed: no changed path may silently run zero tests.

### Required tests

- mapping covers every role/test pair; add a coverage assertion against the
  actual `tests/` tree.
- unknown path → full-fast fallback.
- gate-map/Makefile change → full-fast fallback.
- changed role → only mapped tests plus global checks.
- working-tree/staged changes are included, not just committed commits.
- `BASE` resolution prints the chosen base and fails clearly if it cannot be
  resolved.
- `make dev` does not alter the authoritative `GATES` list or CI parity.

## Non-goals

- No weakening of `make gates`; release/PR still run the full suite.
- No coverage-cache/testmon-only correctness. Path mapping must be explicit and
  deterministic.
- No CI sharding or test-suite parallelization in this ticket.
- No release-preflight script in this ticket (separate follow-up).
- No changes to tests' assertions or production behavior.

## Implementation steps

1. Add `scripts/gate_diff.py` and `scripts/gate-map.yaml` (or equivalent
   explicit map).
2. Add `make dev` and `make gates-role`; keep `GATES` untouched.
3. Add `tests/unit/test_gate_diff.py` with the fail-closed cases.
4. Update `Makefile` help and `AGENTS.md` / developer docs to state:
   dev mode is feedback only; release mode is authoritative.
5. Run the new tests, lint, docs-check, and a representative diff-mode command.
6. Commit as one implementation change; no tag required for this feature unless
   the repo release flow requires it.

## Acceptance

- [ ] `make dev` runs mapped tests plus cheap global checks and reports the
  mapping.
- [ ] Unknown paths, gate-map changes, and Makefile changes fall back to the
  full fast suite.
- [ ] A role-only change does not run the whole engine suite.
- [ ] `make gates` and `ci-gates-parity` are unchanged.
- [ ] `tests/unit/test_gate_diff.py` covers mapping coverage and all fallback
  cases.
- [ ] Documentation says dev mode is not release proof.

## Expected impact

- development feedback: from tens of minutes to seconds/minutes for scoped
  changes
- release candidates: still one full authoritative gate
- no reduction in release coverage
