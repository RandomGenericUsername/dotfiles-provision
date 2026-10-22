# Tasks

## 1. Import and scaffold (≤2h)

- [x] 1.1 Create the public repo and push the imported provisioning history plus the mu harness
  seed as `main`; verify the imported base is present.
  Verify: `git log --oneline | wc -l` → ≥ 2; `gh repo view RandomGenericUsername/dotfiles-provision
  --json visibility --jq .visibility` → `PUBLIC`.
- [x] 1.2 Copy the mu harness byte-for-byte (`scripts/worktree-guard.sh`, `skills-lock.json`,
  `_bmad/`, `.agents/skills/`, `.opencode/`, `tickets/_template/`, `tickets/_fixtures/`,
  `tickets/LIFECYCLE.md`).
  Verify: `diff` against `/home/inumaki/Development/mu/<path>` for each → empty, exit 0; `test -x
  scripts/worktree-guard.sh` → exit 0.
- [x] 1.3 Write `AGENTS.md` (evidence rule, engine charter, seam rule, ticket routing, worktree
  discipline, planning-vs-implementation, release ritual) and `CLAUDE.md` → `AGENTS.md`.
  Verify: `test -L CLAUDE.md` → exit 0; `rg -c "Evidence:|Verify:" AGENTS.md` → ≥ 2.

## 2. Composition seam (≤3h)

- [x] 2.1 Add `--manifests-dir`, `--composition-root` and `--inventory` to the CLI; resolve and
  validate the seam once; pass `manifests_dir` / `composition_root` as extra-vars; add the
  `manifests` read-only command.
  Verify: `uv run dotfiles-provision --output-format json --manifests-dir
  tests/fixtures/composition/dotfiles/provisioning manifests` → `count: 5`, exit 0.
- [x] 2.2 Replace every `{{ playbook_dir }}/../../../..` derivation in `assets`,
  `compositor_configs`, `config_copies`, `btop_config`, `cli_tools`, `gui_tools`, `zsh_config`,
  `wlogout_config` (and `runtime-seed`) with a seam value or a pinned-asset path; add fail-loud
  asserts where a role reads the composition.
  Verify: `rg -n "playbook_dir" ansible/` → comments only; `uv run pytest -q
  tests/unit/test_composition_seam.py` → exit 0.
- [x] 2.3 Adapt the moved tests to the engine repo: `tests/support.py` resolution, fixture
  composition tree, no absolute dotfiles paths; keep `cli-output` a git-tag pin.
  Verify: `uv run pytest -q -m "not integration and not container_target"` → exit 0;
  `uv lock --check` → exit 0.

## 3. Ledger and specs (≤2h)

- [x] 3.1 Add `tickets/INDEX.md` with the counting-rule header and `tickets/REQ-001-repo-birth/`.
  Verify: `rg -n "REQ-001" tickets/INDEX.md tickets/REQ-001-repo-birth/ticket.md` → both hit.
- [x] 3.2 Add `openspec/config.yaml`, `openspec/specs/repo-harness/spec.md`, and the `repo-birth`
  change (proposal, design, tasks, spec delta).
  Verify: `openspec validate --all --strict` → exit 0.

## 4. Gates and release (≤2h)

- [x] 4.1 Add the fresh-clone `Makefile` and `scripts/ci-gates-parity.py`; make every verb run
  from `$(CURDIR)`.
  Verify: `make gates` → exit 0; `make ci-gates-parity` → `PASS ...`.
- [x] 4.2 Add `.github/workflows/gates.yml` with one job per gate, `ci-gates-parity`, and a
  tag-only `release` job.
  Verify: `make ci-gates-parity` → exit 0 (the workflow is parsed, not grepped).
- [x] 4.3 Prove packaging: `uv sync --frozen`, `uv run pytest -q`, `uv lock --check`, `uv build`.
  Verify: exit 0; `ls dist/dotfiles_provision-0.1.0-*` lists a wheel and an sdist.
- [x] 4.4 Tag annotated `v0.1.0` after the gates and CI exist; push the tag; confirm the Release
  carries both artifacts.
  Verify: `GIT_TERMINAL_PROMPT=0 git -c credential.helper= ls-remote
  https://github.com/RandomGenericUsername/dotfiles-provision 'refs/tags/v0.1.0'` → exactly one
  line; `gh release view v0.1.0 --json assets --jq '.assets[].name'` → wheel + sdist.

## 5. Closeout (≤0.5h)

- [x] 5.1 Tick acceptance, record commands + results in the ticket, move the INDEX entry to Done.
  Verify: `git status --porcelain` → empty after the merge; `rg -n "REQ-001" tickets/INDEX.md` →
  the Done section lists it.
