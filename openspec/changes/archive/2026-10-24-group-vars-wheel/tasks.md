# Tasks

## 1. Layout and tests (≤1h)

- [x] 1.1 Move `ansible/group_vars/*.yml` to `ansible/inventory/group_vars/`;
  remove the `ansible/group_vars` symlink.
  Verify: `test -f ansible/inventory/group_vars/all.yml && test ! -L ansible/group_vars` → exit 0.
- [x] 1.2 Update `tests/unit/test_ansible_scaffold.py` to read
  `ansible/inventory/group_vars/*`; update the `ansible.cfg` comment.
  Verify: `uv run pytest -q tests/unit/test_ansible_scaffold.py` → exit 0.

## 2. Build proof (≤1h)

- [x] 2.1 Add `scripts/check-wheel-contents.py`; call it from `make build`.
  Verify: `make build` → `PASS: ... carries the Ansible tree + inventory/group_vars`.
- [x] 2.2 Bump `pyproject.toml` to `0.1.9`; add the `CHANGELOG.md` entry.
  Verify: `uv lock --check`; `rg -n "0.1.9" pyproject.toml CHANGELOG.md`.

## 3. Release (≤2h)

- [x] 3.1 `make gates`, `make build`; record counts.
- [x] 3.2 Tag annotated `v0.1.9`, push, confirm CI + Release artifacts.
- [x] 3.3 Close BUG-002, archive this change, bump the composition pin to
  `v0.1.9`, and run a real `make provision ARGS="verify --expected-engine-tag v0.1.9"`.
