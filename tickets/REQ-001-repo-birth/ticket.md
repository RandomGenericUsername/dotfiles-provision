---
id: REQ-001
title: "Birth the dotfiles-provision engine (mu-strict) with the composition seam and cut v0.1.0"
kind: requirement
status: in-progress
lane: 3
links:
  openspec: repo-birth
  bmad: none
worktree: .worktrees/req-001/
branch: ticket/req-001-installer-engine-birth
---

# Birth the dotfiles-provision engine (mu-strict) with the composition seam and cut v0.1.0

## Requirement

Slice **S6a** of the CLI/installer split SHALL create `RandomGenericUsername/dotfiles-provision`
as a public repo whose root carries the extracted provisioning tree (`ansible/`,
`src/provisioning/`, `tests/`), install the `mu` harness byte-for-byte, and cut the repo's first
tag (`v0.1.0`) only after the gates, packaging and CI exist.

The engine is **not** a composition checkout. It owns the Ansible tree and the Python
orchestrator; the composition repo owns the manifests and the runtime. The load-bearing change is
therefore the **composition seam (AD-17)**: every composition path is supplied by the CLI
(`--manifests-dir`, `--composition-root`) and passed to Ansible as extra-vars. No role derives a
composition path from `{{ playbook_dir }}` — a fresh engine clone has no composition ancestors.

This slice changes no provisioning behaviour: the same roles, tasks, manifests and done-criteria.
`dotfiles-v3` is not modified — rewiring its consumer pins and deleting its in-tree
`src/provisioning/` are a later step in that repo.

## Acceptance

- [x] The repo exists, is **public**, and `main` carries the imported history plus the harness
  seed. Verify: `gh api repos/RandomGenericUsername/dotfiles-provision --jq .private` → `false`;
  `git log --oneline | wc -l` → ≥ 2.
- [x] The harness is byte-identical to `mu` at every copied path. Verify: `diff` per path
  (`scripts/worktree-guard.sh`, `skills-lock.json`, `_bmad/`, `.agents/skills/`, `.opencode/`,
  `tickets/_template/`, `tickets/_fixtures/`, `tickets/LIFECYCLE.md`) → empty, exit 0.
- [x] `AGENTS.md` carries the evidence rule and the engine charter; `CLAUDE.md` is a symlink.
  Verify: `rg -c "Evidence:|Verify:" AGENTS.md` → ≥ 2; `test -L CLAUDE.md` → exit 0.
- [x] The composition seam is complete: no `playbook_dir`-derived composition path remains, and
  an external `--manifests-dir` resolves every manifest. Verify:
  `rg -n "playbook_dir" ansible/` → comments only (no task/var value); `uv run pytest -q
  tests/unit/test_composition_seam.py` → exit 0, every manifest resolved from the engine cwd.
- [x] `tickets/INDEX.md` lists this ticket with the same status as the frontmatter; the OpenSpec
  change validates strictly. Verify: `openspec validate repo-birth --strict` → exit 0;
  `openspec validate --all --strict` → exit 0.
- [x] A fresh clone passes `make sync && make gates && make hermetic && uv lock --check && uv
  build`, and builds both artifacts. Verify: exit 0; `ls dist/dotfiles_provision-0.1.0-*` → wheel
  + sdist.
- [x] `.github/workflows/gates.yml` exists and its job set equals `GATES` (plus declared CI-only
  jobs); the first run on `main` is green. Verify: `make ci-gates-parity` → `PASS ...`;
  `gh run list -R RandomGenericUsername/dotfiles-provision --limit 1 --json status,conclusion` →
  `completed` / `success`.
- [x] Annotated tag `v0.1.0` exists on the released commit, is anonymously fetchable, and its
  GitHub Release carries the wheel + sdist. Verify: `GIT_TERMINAL_PROMPT=0 git -c
  credential.helper= ls-remote https://github.com/RandomGenericUsername/dotfiles-provision
  'refs/tags/v0.1.0'` → one line; `gh release view v0.1.0 --json assets --jq '.assets[].name'` →
  both artifacts.
- [x] `git status --porcelain` is empty in both repos; `dotfiles-v3` is unchanged by this slice.
  Verify: `git status --porcelain` → empty; `git -C /home/inumaki/Development/dotfiles/dotfiles-v3
  status --porcelain` → empty.

## Out of scope

- Rewiring `dotfiles-v3` (its `src/provisioning` consumer, pin bump, deletion of the in-tree
  provisioning tree) and any change to its manifests or runtime. Those are the remaining S6 steps
  in that repo.
- Any role/task behaviour change, dependency change, or composition manifest change.
- Making the built wheel self-contained: the Ansible tree is not package data, so consumers
  install from a pinned checkout, not from a wheel (documented in `README.md`).
- PyPI publication; the channel is the git tag plus GitHub Release artifacts.

## Closeout

Closed on `ticket/req-001-installer-engine-birth` (worktree `.worktrees/req-001/`), fast-forwarded
onto `main`. Evidence (commands run from the repo root unless a path is named) is recorded below
at closeout time.

| Claim | Command | Result |
| --- | --- | --- |
| Repo is public | `gh api repos/RandomGenericUsername/dotfiles-provision --jq .private` | `false`, exit 0 |
| Harness byte-identical | `diff -r /home/inumaki/Development/mu/<path> <path>` for the eight copied paths | empty output, exit 0 for all eight |
| Seam guard | `uv run pytest -q tests/unit/test_composition_seam.py` | see closeout |
| Gates (local clone) | `make sync && make gates` | see closeout |
| Hermetic | `make hermetic` | see closeout |
| Lock current | `uv lock --check` | see closeout |
| Build | `uv build` | see closeout |
| Specs valid | `openspec validate --all --strict` | see closeout |
| Workflow ↔ Makefile parity | `make ci-gates-parity` | see closeout |
| Tag object / peeled commit | `git rev-parse v0.1.0`; `git rev-parse 'v0.1.0^{commit}'` | see closeout |
| CI | `gh run list -R RandomGenericUsername/dotfiles-provision --limit 1` | see closeout |
| `dotfiles-v3` untouched | `git -C /home/inumaki/Development/dotfiles/dotfiles-v3 status --porcelain` | see closeout |
