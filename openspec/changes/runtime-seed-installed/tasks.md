# Tasks

## 1. Fix (≤1h)

- [ ] 1.1 Add `runtime_seed_bin_dir` and invoke `{{ runtime_seed_bin_dir }}/dotfiles-runtime`
  in `ansible/playbooks/runtime-seed.yaml`; remove the `composition_root` assert and the
  `src/runtime` comment.
  Verify: `rg -n 'src/runtime|uv run --directory' ansible/playbooks/runtime-seed.yaml` → no matches.
- [ ] 1.2 Add `tests/unit/test_runtime_seed_playbook.py`: the seed argv starts with the installed
  binary, the task is check-gated, and the playbook text names no composition source path.
  Verify: `uv run pytest -q tests/unit/test_runtime_seed_playbook.py` → exit 0.
- [ ] 1.3 Update the integration/seam docstrings that still claim the seed runs the composition's
  `src/runtime`.
  Verify: `rg -n 'src/runtime' tests ansible/playbooks/runtime-seed.yaml` → no matches in the
  seed/test descriptions.

## 2. Release (≤2h)

- [ ] 2.1 Bump `pyproject.toml` to `0.1.8`; add the `CHANGELOG.md` entry.
- [ ] 2.2 `make gates`, `make build`; record counts.
  Verify: exit 0; `ls dist/dotfiles_provision-0.1.8-*`.
- [ ] 2.3 Tag annotated `v0.1.8`, push, confirm CI + Release artifacts.
  Verify: `gh release view v0.1.8 --json assets`.

## 3. Closeout (≤0.5h)

- [ ] 3.1 Close the bug ticket, archive the OpenSpec change, and bump the composition's
  `installer.pin` to `v0.1.8` in a separate commit there.
  Verify: `openspec validate runtime-seed-installed --strict`; composition `make deploy-coverage`.
