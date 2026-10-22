# repo-birth

## Why

`dotfiles-provision` is the provisioning engine extracted from `dotfiles-v3` in the
CLI/installer split programme. The provisioning tree already exists and is green in-tree, but a
repository is not a valid extraction target until it is mu-strict from its first commit (spine
AD-12: "harness later" is exactly the failure the guide names). The extraction also exposes the
one contract the in-tree layout hid: the engine has **no composition checkout above it**, so every
composition path must come from the CLI instead of a `playbook_dir` climb.

Evidence: the engine content is the in-tree provisioning project — `ansible/` (21 roles,
23 playbooks), `src/provisioning/` (hexagonal Python), `tests/` and `pyproject.toml` — imported
with history preserved.
Verify: `git log --oneline | tail -1` names the imported seed commit; `ls ansible/roles | wc -l` →
`21`.

Evidence: the composition owns the manifests, not the engine.
Verify: `ls dotfiles/provisioning` in the engine → absent; the same path under
`/home/inumaki/Development/dotfiles/dotfiles-v3` → five `*.yaml` manifests.

Evidence: the harness must be copied from `mu`, not re-authored (AD-12).
Verify: `diff -r /home/inumaki/Development/mu/tickets/_template tickets/_template` → empty; same
for `tickets/_fixtures/` and `tickets/LIFECYCLE.md`.

## What Changes

- Publish `RandomGenericUsername/dotfiles-provision` as a public repo, default branch `main`,
  carrying the imported provisioning history plus a byte-copied `mu` harness seed.
- Install the mu-strict harness **byte-for-byte**: `scripts/worktree-guard.sh`, `skills-lock.json`,
  `_bmad/`, `.agents/skills/`, `.opencode/`, `tickets/_template/`, `tickets/_fixtures/`,
  `tickets/LIFECYCLE.md`.
- Implement the **composition seam (AD-17)**: the CLI resolves `--manifests-dir`,
  `--composition-root` and `--inventory` once, validates them, and passes
  `manifests_dir` / `composition_root` as extra-vars. Remove every
  `{{ playbook_dir }}/../../../..` repo-root derivation from `assets`, `compositor_configs`,
  `config_copies`, `btop_config`, `cli_tools`, `gui_tools`, `zsh_config`, `wlogout_config`.
- Add the repo contract: `AGENTS.md` (evidence rule, engine charter, seam rule, ticket routing,
  never work on main, planning vs implementation, release ritual), `CLAUDE.md` → `AGENTS.md`.
- Add the work ledger: `tickets/INDEX.md` (counting-rule header), `tickets/REQ-001-repo-birth/`.
- Add the OpenSpec root: `openspec/config.yaml`, `openspec/specs/repo-harness/`, and this change.
- Add a fresh-clone Makefile (`sync`, `test`, `lint`, `format`, `hermetic`, `lock-check`,
  `docs-check`, `gates`, `gates-ci`, `build`, `install`, `clean`, `ci-gates-parity`,
  `test-integration`), `.github/workflows/gates.yml` (one job per gate + `ci-gates-parity` +
  tag release), `scripts/ci-gates-parity.py`, MIT `LICENSE`, `README.md`, `CHANGELOG.md`,
  `.gitignore`.
- Adapt the moved tests: manifests are read from `tests/fixtures/composition/` (or
  `$DOTFILES_COMPOSITION_ROOT`), never from a dotfiles checkout above the engine; add the seam
  guard test; keep `cli-output` as a git-tag pin and keep `uv.lock` clean.

## Capabilities

- **New Capabilities:** `repo-harness` — the repo contract, ticket ledger, OpenSpec root, seam
  guard, gate set and release ritual that make this repo a valid extraction target.

- **Modified Capabilities:** none. The manifest shapes, role behaviour and done-criteria are
  unchanged; only the source of composition paths changes.

## Non-goals (out of scope)

- **Not** rewiring `dotfiles-v3`: no consumer pin bump, no deletion of its in-tree
  `src/provisioning/`, no manifest edit. That is the next slice step in that repo.
- **Not** changing provisioning behaviour: no role semantics, done-criterion, dependency or
  manifest shape change.
- **Not** making the wheel self-contained: the Ansible tree is not package data, so the release
  artifacts are for inspection/record; consumers pin a checkout (documented in `README.md`).
- **Not** publishing to PyPI: the release channel is a git tag plus GitHub Release artifacts.

## Impact

- New: `AGENTS.md`, `CLAUDE.md` (symlink), `Makefile`, `LICENSE`, `CHANGELOG.md`,
  `.github/workflows/gates.yml`, `scripts/ci-gates-parity.py`, `openspec/`, `tickets/`,
  `tests/support.py`, `tests/fixtures/composition/`, `tests/unit/test_composition_seam.py`, and
  the copied harness support files.
- Modified: `src/provisioning/application/use_cases.py`, `src/provisioning/cli/{main,options}.py`,
  `ansible/group_vars/all.yml`, `ansible/playbooks/runtime-seed.yaml`, the eight role
  vars/tasks/templates carrying a repo-root derivation, the moved tests, and `pyproject.toml`
  (readme/license metadata, test marker defaults, sdist `only-include`).
- Unchanged: every manifest shape, role behaviour and done-criterion; `dotfiles-v3` itself.
