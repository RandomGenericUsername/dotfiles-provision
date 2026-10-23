# AGENTS.md — dotfiles-provision operating contract

Canonical agent instructions for this repo. Claude (`CLAUDE.md` symlinks here), OpenCode, and all
BMAD/OpenSpec skills must follow this.

## 1. Evidence rule (hard requirement)

No suggestion "in the air". Every technical claim, recommendation, or design decision must carry
testable evidence — at least one of:

- **Doc evidence:** file path + line range, or commit SHA, or URL + quoted section.
- **Prototype evidence:** a script/command in-repo that runs and prints the validating output.
  State the exact command and observed result.
- **Test evidence:** `command run → result` (exit code + key output). Failing-as-expected counts
  if it validates the claim.

Format: any non-trivial claim gets an `Evidence:` line and a `Verify:` line (how to reproduce in
one command). If evidence doesn't exist yet, say `Evidence: MISSING — run <X> to produce it` and
do not present the claim as fact.

## 2. Charter — the installer ENGINE, not the composition

- This repo owns the provisioning **engine**: the Ansible tree (`ansible/`) and the Python
  orchestrator (`src/provisioning/`) that runs it. One package, repo root = package root:
  `src/provisioning/`, `ansible/`, `tests/` at the top level, no nested project roots.
  Evidence: `pyproject.toml` `[tool.hatch.build.targets.wheel] packages = ["src/provisioning"]`.
- The **composition** repo (`dotfiles-v3`) owns the manifests (`dotfiles/provisioning/*.yaml`),
  the provisioning scripts and `src/runtime/`. The btop active-theme preference is host state in
  the install spine (R-07), not a composition file. This repo ships none of them.
  Evidence: `ls ansible/roles` has no manifest tree; `tests/fixtures/composition/README.md`
  documents the fixture standing in for the composition in tests.
- **The composition seam (AD-17).** The engine learns composition paths ONLY from the CLI:
  `--manifests-dir` (default `<cwd>/dotfiles/provisioning`) and `--composition-root` (default the
  manifests dir's grandparent), passed to Ansible as the `manifests_dir` / `composition_root`
  extra-vars. **No role may derive a composition path from `{{ playbook_dir }}`** — a pinned
  engine checkout has no composition ancestors. Guard:
  `tests/unit/test_composition_seam.py::TestNoRoleDerivesFromPlaybookDir`.
- Consumers pin this repo as an immutable git tag, never a path, never `editable = true`, never a
  branch. No consumer may read this repo's tests or fixture composition at runtime.

## 3. How we work here

- Read files, run commands (`rg`, `git log`, `uv`, `openspec validate`), paste results. Prefer
  executed output over recalled text.
- When findings contradict an earlier claim, state the discrepancy and trust the evidence.
- Keep changes small, verifiable, committable. A suite that is green only on the author's host is
  not green: tests resolve the composition through `tests/support.py` (fixture by default,
  `$DOTFILES_COMPOSITION_ROOT` to check against a real checkout), and `make hermetic` runs the
  suite with empty `HOME` / `XDG_*` and a throwaway cwd.

## 4. Worktree discipline — never work on `main`

- `bash scripts/worktree-guard.sh check-clean` aborts when `main` is dirty.
- `bash scripts/worktree-guard.sh create <id> <slug>` creates `.worktrees/<id>/` on
  `ticket/<id>-<slug>`. Merge back to `main` only when the gates are green.
- Planning edits (tickets/specs) and implementation edits land in **separate commits**.

## 5. Gates and release

- `make gates` = `test lint hermetic lock-check docs-check` (the authoritative list is `GATES` in
  the `Makefile`). CI runs one job per gate (`.github/workflows/gates.yml`) and
  `make ci-gates-parity` fails when the two sets differ.
- `make test` runs the fast suite (`-m "not integration and not container_target"`);
  `make test-integration` runs the real-`ansible-playbook` suite for a developer machine.
- A release is an annotated `vMAJOR.MINOR.PATCH` tag plus a GitHub Release carrying the sdist and
  wheel built from that commit. Tags are never moved or deleted. PyPI is not used.

## 6. Ticket / OpenSpec routing

- All work starts as a ticket in `tickets/` (`_template/`, vocab + rollup in `INDEX.md`, flow in
  `LIFECYCLE.md`).
- A capability change updates `openspec/specs/`; a change in flight lives in `openspec/changes/`
  and must pass `openspec validate <change> --strict` before it is archived.
