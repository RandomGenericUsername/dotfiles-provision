# Tasks

## 1. Role and verify (≤2h)

- [x] 1.1 Mirror `dotfiles-runtime` as `{repo, tag: v0.1.0}` in
  `ansible/roles/cli_tools/vars/main.yml`; update the mixed-shape comments.
  Verify: `rg -n "dotfiles-runtime" ansible/roles/cli_tools/vars/main.yml` → one pinned entry.
- [x] 1.2 Add `dotfiles-runtime` to `verify_cli_tools` and the runtime version/checkout/pin vars.
  Verify: `rg -n "verify_runtime" ansible/roles/verify/vars/main.yml` → all four.
- [x] 1.3 Add the runtime verify block (stat, slurp, `version`, assert) to
  `ansible/roles/verify/tasks/main.yml`; update the PATH failure message.
  Verify: `rg -n "pinned dotfiles-runtime" ansible/roles/verify/tasks/main.yml` → block present.

## 2. Fixture and tests (≤2h)

- [x] 2.1 Update `tests/fixtures/composition/dotfiles/provisioning/cli-tools.yaml`; remove
  `tests/fixtures/composition/src/runtime/pyproject.toml`; update the fixture README and
  `tests/support.py` prose.
  Verify: `rg -n "source: src/runtime" tests/fixtures` → no matches.
- [x] 2.2 Update `tests/unit/test_cli_tools_role.py`: all-pinned expectations, no source entry,
  runtime repo/tag assertions; the source-path task still exists with an empty loop.
  Verify: `uv run pytest -q tests/unit/test_cli_tools_role.py` → exit 0.
- [x] 2.3 Update `tests/unit/test_verify_role.py`: the PATH list includes runtime; the pin mirror
  loop includes runtime; add the runtime verify-block assertions.
  Verify: `uv run pytest -q tests/unit/test_verify_role.py` → exit 0.

## 3. Docs and release (≤2h)

- [x] 3.1 Update `README.md`, `AGENTS.md`, `ansible/group_vars/all.yml`,
  `src/provisioning/{application/use_cases.py,cli/options.py}` prose that names `src/runtime/`.
  Verify: `rg -n "src/runtime/" README.md AGENTS.md ansible/group_vars/all.yml src/provisioning` →
  no stale "still authors" claims.
- [x] 3.2 Bump `pyproject.toml` to `0.1.7`, add the `CHANGELOG.md` entry.
  Verify: `uv lock --check`; `rg -n "0.1.7" pyproject.toml CHANGELOG.md`.
- [x] 3.3 Run `make gates`, `make build`; record counts.
  Verify: exit 0; `ls dist/dotfiles_provision-0.1.7-*`.
- [x] 3.4 Tag annotated `v0.1.7`, push, confirm CI + Release artifacts.
  Verify: `gh release view v0.1.7 --json assets`.

## 4. Closeout (≤0.5h)

- [x] 4.1 Close the ticket and move the INDEX entry to Done; archive the OpenSpec change.
  Verify: `openspec validate --all --strict`; `rg -n "REQ-002" tickets/INDEX.md`.
