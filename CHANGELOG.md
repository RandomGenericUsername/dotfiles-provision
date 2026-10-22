# Changelog

Notable changes to the `dotfiles-provision` repo. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow the git tags
(`vMAJOR.MINOR.PATCH`, annotated, never moved).

## [Unreleased]

## [0.1.0] - 2026-10-22

First release. The engine content is the in-tree provisioning project imported from
`dotfiles-v3` (`ansible/`, `src/provisioning/`, `tests/`), history preserved.

### Added

- The provisioning engine at the repo root: 21 Ansible roles, 23 playbooks, the hexagonal Python
  orchestrator (`plan` / `apply` / `verify` / `bootstrap`), and the seam contract that wires them.
- The **composition seam** (AD-17): `--manifests-dir`, `--composition-root` and `--inventory`
  resolved once by the CLI and passed to Ansible as `manifests_dir` / `composition_root`
  extra-vars. The read-only `manifests` command resolves every manifest through the real reader.
- `tests/support.py` and `tests/fixtures/composition/`: the moved unit tests resolve the
  composition from a byte-copied fixture (or `$DOTFILES_COMPOSITION_ROOT`), never from a dotfiles
  checkout above the engine.
- `tests/unit/test_composition_seam.py`: the executable seam guard (external manifests dir, loud
  failures, and a static scan proving no YAML value or Jinja template derives from
  `playbook_dir`).
- Repo harness copied byte-for-byte from `mu`: `scripts/worktree-guard.sh`, `skills-lock.json`,
  `_bmad/`, `.agents/skills/`, `.opencode/`, `tickets/_template/`, `tickets/_fixtures/`,
  `tickets/LIFECYCLE.md`.
- `Makefile` fresh-clone verbs (`sync`, `test`, `test-integration`, `lint`, `format`, `hermetic`,
  `lock-check`, `docs-check`, `gates`, `gates-ci`, `build`, `install`, `clean`,
  `ci-gates-parity`), `.github/workflows/gates.yml`, and `scripts/ci-gates-parity.py`.
- MIT `LICENSE`, `README.md`, `AGENTS.md`, `CLAUDE.md` symlink, ticket `REQ-001-repo-birth`, and
  the OpenSpec change `repo-birth` plus the `repo-harness` spec.

### Changed

- Every `{{ playbook_dir }}/../../../..` repo-root derivation is gone: `btop_config` and
  `cli_tools` read the seam, `runtime-seed` runs the composition's runtime through
  `composition_root`, and the pinned-asset roles (`assets`, `compositor_configs`,
  `config_copies`, `gui_tools`, `zsh_config`, `wlogout_config`) read their checkouts instead.
- `pyproject.toml`: release metadata (`readme`, license classifier) and an sdist `only-include`
  that keeps the harness trees out while shipping `ansible/` for source installs.
- Tests that asserted the composition's provisioning-shape gate or `bootstrap.sh` were retired
  from this repo (they belong to `dotfiles-v3`); the manifest-parity tests now read the fixture.
