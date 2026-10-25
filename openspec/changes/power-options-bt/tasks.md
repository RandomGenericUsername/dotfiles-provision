# Tasks

## 1. Role and playbook (≤1h)

- [ ] 1.1 Add `ansible/roles/power_options/{vars,tasks}` and
  `ansible/playbooks/power-options.yaml` (become).
  Verify: `uv run pytest -q tests/unit/test_power_options_role.py` → exit 0.
- [ ] 1.2 Import `power-options.yaml` in `bootstrap.yaml` after `packages`; update the
  bootstrap order/count test.
  Verify: `uv run pytest -q tests/unit/test_bootstrap_playbook.py` → exit 0.

## 2. Verify and docs (≤1h)

- [ ] 2.1 Add `verify_power_options_*` vars/tasks (read the three profiles, assert false, skip
  when the directory is absent).
  Verify: `uv run pytest -q tests/unit/test_power_options_role.py tests/unit/test_verify_role.py -k power_options` → exit 0.
- [ ] 2.2 Bump `pyproject.toml` to `0.1.10`, add the `CHANGELOG.md` entry.
  Verify: `uv lock --check`.

## 3. Release (≤2h)

- [ ] 3.1 `make gates`, `make build`; record counts.
- [ ] 3.2 Tag annotated `v0.1.10`, push, confirm CI + Release artifacts.
- [ ] 3.3 Close REQ-003, archive this change, bump the composition pin to `v0.1.10`, run
  `make deploy-coverage` + `make gates-ci`.
- [ ] 3.4 Apply the playbook on the host (or run bootstrap), confirm
  `grep block_bt /etc/power-options/profiles/*.toml` is all false and full `verify` passes.
