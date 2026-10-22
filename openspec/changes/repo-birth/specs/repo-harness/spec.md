# repo-harness (delta)

## ADDED Requirements

### Requirement: the mu harness is present and byte-identical

The repo SHALL contain `scripts/worktree-guard.sh` (executable), `skills-lock.json`, `_bmad/`,
`.agents/skills/`, `.opencode/`, `tickets/_template/`, `tickets/_fixtures/` and
`tickets/LIFECYCLE.md`, each byte-identical to `/home/inumaki/Development/mu`.

Source: spine AD-12; `mu/AGENTS.md` §2; `ARCHITECTURE-SPINE.md` § Repo Birth Checklist items 3–6.

#### Scenario: guard is executable and clean-tree safe

- **WHEN** `bash scripts/worktree-guard.sh check-clean` runs on a clean tree
- **THEN** it exits 0

#### Scenario: a dirty tree is refused

- **WHEN** any tracked file is modified and `check-clean` runs
- **THEN** it exits 1 and prints `main is dirty, address it first`

#### Scenario: copied trees match their source

- **WHEN** `diff -r /home/inumaki/Development/mu/tickets/_template tickets/_template` runs
- **THEN** the output is empty and the exit code is 0

### Requirement: composition paths come only from the CLI seam

The engine SHALL resolve composition paths exclusively from `--manifests-dir` and
`--composition-root` (and the inventory from `--inventory`), pass `manifests_dir` and
`composition_root` to Ansible as extra-vars, and SHALL NOT contain a role, task, playbook or
template that derives a composition path from `playbook_dir`.

Source: spine AD-17; `AGENTS.md` §2; `openspec/config.yaml` context.

#### Scenario: an external manifests dir resolves every manifest

- **WHEN** `dotfiles-provision --manifests-dir <external>/dotfiles/provisioning manifests` runs
  from the engine root (which has no `dotfiles/` child)
- **THEN** it exits 0 and reports all five manifests with their kinds

#### Scenario: a bad path fails before Ansible starts

- **WHEN** `--manifests-dir` points at a directory that does not exist
- **THEN** the command exits 2 with `kind: CompositionPathError` naming the flag

#### Scenario: no playbook-dir derivation remains

- **WHEN** every YAML value and every `.j2` template under `ansible/` is scanned for
  `playbook_dir` and a four-level `../../../../` climb
- **THEN** no occurrence exists

#### Scenario: direct playbook runs fail loud without the seam

- **WHEN** a role that reads the composition runs without `manifests_dir` / `composition_root`
- **THEN** its first task asserts and fails with a message naming the flag to pass

### Requirement: a fresh clone passes the gate set

`make sync && make gates && make build` SHALL exit 0 on a fresh clone, where
`GATES = test lint hermetic lock-check docs-check`, and `hermetic` SHALL pass with `HOME` and all
four `XDG_*` variables pointed at empty temp dirs.

Source: spine AD-8, AD-12, AD-14; birth checklist items 9–11.

#### Scenario: gates on a fresh clone

- **WHEN** `git clone <repo> /tmp/x && cd /tmp/x && make sync && make gates` runs
- **THEN** every gate exits 0; `make hermetic` runs the same selection from an unrelated cwd and
  the corpus-dependent tests that need a pinned `dotfiles-assets` checkout or a provisioned spine
  SKIP with their stated reason (never pass vacuously)

#### Scenario: build produces both artifacts

- **WHEN** `make build` runs
- **THEN** `dist/dotfiles_provision-0.1.0-*.whl` and `dist/dotfiles_provision-0.1.0.tar.gz` exist

#### Scenario: workflow and Makefile agree

- **WHEN** `make ci-gates-parity` runs
- **THEN** it prints `PASS ...` and exits 0; adding a gate without a job (or the reverse) exits 1

### Requirement: a release is a tag with reproducible artifacts

An annotated `vMAJOR.MINOR.PATCH` tag SHALL be created only after the gates are green,
`CHANGELOG.md` SHALL describe the release, and CI SHALL attach the sdist and wheel built from
that commit to the GitHub Release. A published tag is never moved or deleted.

Source: spine AD-9; OPEN-3 (git-tag-only, no PyPI); OPEN-5 (MIT `LICENSE` before the first tag).

#### Scenario: the first tag resolves to one commit

- **WHEN** `git ls-remote --tags origin v0.1.0` runs with credentials disabled
- **THEN** it prints exactly one line ending in `refs/tags/v0.1.0`, and
  `git rev-parse v0.1.0^{commit}` names the released commit

#### Scenario: the release carries both artifacts

- **WHEN** `gh release view v0.1.0 --json assets --jq '.assets[].name'` runs
- **THEN** it lists `dotfiles_provision-0.1.0-py3-none-any.whl` and
  `dotfiles_provision-0.1.0.tar.gz`
