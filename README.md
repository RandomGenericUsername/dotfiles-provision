# dotfiles-provision

The provisioning **engine** for the dotfiles system: a hexagonal Python orchestrator
(`plan` / `apply` / `verify` / `bootstrap`) over an Ansible tree that establishes the machine
state the runtime assumes exists — packages, CLI tools, pinned assets, filesystem spine, rendered
settings and the desktop session.

**Charter — the engine, not the composition.** This repo owns `ansible/` and
`src/provisioning/`. The composition repo (`dotfiles-v3`) owns the manifests
(`dotfiles/provisioning/*.yaml`), the provisioning scripts, `dotfiles/config/btop/active-theme`
and `src/runtime/`. The engine never ships or edits them; it reads them through the CLI seam
below.

## The composition seam (AD-17)

A pinned engine checkout has **no composition ancestors**, so no role derives a composition path
from `{{ playbook_dir }}`. The CLI resolves the paths once and passes them to Ansible as
extra-vars:

| Flag | Default | Extra-var | Used for |
| --- | --- | --- | --- |
| `--manifests-dir` | `<cwd>/dotfiles/provisioning` | `manifests_dir` | manifest validation, `scripts/gloview-activate` |
| `--composition-root` | parent of `--manifests-dir`'s parent | `composition_root` | `dotfiles/config/btop/active-theme`, `src/runtime/` |
| `--inventory` | this engine's `ansible/inventory/localhost.yaml` | (executor `-i`) | the host Ansible runs against |

Flags are global (before the command). A bad path fails before Ansible starts with a structured
`CompositionPathError` (exit 2). A direct `ansible-playbook` run that omits the extra-vars fails
loud in the consuming role's first assert instead of reading the engine checkout.

`dotfiles-provision manifests` is the read-only seam check: it resolves every `*.yaml` in
`--manifests-dir` through the real manifest reader and prints the kinds.

```bash
# From a composition checkout (defaults resolve):
dotfiles-provision plan
dotfiles-provision apply --ask-become-pass
dotfiles-provision verify

# From anywhere, pointing at a composition:
dotfiles-provision \
  --manifests-dir /path/to/dotfiles-v3/dotfiles/provisioning \
  --composition-root /path/to/dotfiles-v3 \
  --inventory ansible/inventory/localhost.yaml \
  plan
```

`plan` is Ansible `--check` (no machine changes). `verify` is a real, non-mutating assertion run
against the deployed spine. `apply`/`bootstrap` change the machine.

## Install from a checkout (development)

```bash
make sync                 # uv sync --frozen
make gates                # test + lint + hermetic + lock-check + docs-check
make test-integration     # real ansible-playbook + disposable-container proofs
make build                # sdist + wheel in dist/
```

## Cross-repo pin usage

This repo is consumed as an **immutable git tag**, never a path and never `editable = true`:

```toml
# a consumer's pyproject.toml
[tool.uv.sources]
dotfiles-provision = { git = "https://github.com/RandomGenericUsername/dotfiles-provision", tag = "v0.1.0" }
```

A tag is never moved or deleted; a fix ships as a new tag. The `cli-output` dependency is pinned
the same way in this repo's `pyproject.toml`.

**The wheel is not a self-contained provisioner.** `[tool.hatch.build.targets.wheel]` packages
only `src/provisioning`, and the CLI resolves `ansible/` beside the installed checkout — not in
`site-packages`. Install the engine from the pinned **checkout** (the sdist carries `ansible/` for
source installs); the wheel exists to record the release, not to replace the tree.

## Tests

- The fast suite (`make test`) is hermetic: manifests resolve through `tests/support.py` to
  `tests/fixtures/composition/` (a byte-copied composition subset), or to
  `$DOTFILES_COMPOSITION_ROOT` when set to a real checkout.
- `tests/unit/test_composition_seam.py` is the executable form of AD-17: an external
  `--manifests-dir` resolves every manifest, bad paths fail loud, and no YAML value or Jinja
  template under `ansible/` derives a path from `playbook_dir`.
- `make test-integration` runs the real `ansible-playbook --check` matrix and the disposable
  container proof. The container proof skips loudly unless `$DOTFILES_COMPOSITION_ROOT` names a
  composition with a real runtime.
- `make hermetic` runs the same selection with empty `HOME`/`XDG_*` and a foreign cwd. Tests that
  need the pinned `dotfiles-assets` corpus (a separate repo) skip with their stated reason unless
  `$DOTFILES_ASSETS_REPO`, `$DOTFILES_ASSETS_TEMPLATES_DIR` or a provisioned spine provides it.

## Repo harness

- `AGENTS.md` (with `CLAUDE.md` symlinked to it) is the operating contract: evidence rule,
  engine charter, seam rule, worktree discipline, planning-vs-implementation commits.
- `tickets/` is the work ledger (`INDEX.md`, `LIFECYCLE.md`, `_template/`, `_fixtures/`).
- `openspec/` holds the specs (`config.yaml`, `specs/`) and the change log (`changes/`).
- `scripts/worktree-guard.sh create <id> <slug>` makes `.worktrees/<id>/` on
  `ticket/<id>-<slug>`; never work on `main`.
- `.agents/skills/` + `skills-lock.json` and `_bmad/` are hash-pinned copies of the `mu` harness.

## Release

Version in `pyproject.toml` + `CHANGELOG.md` entry → annotated tag `vX.Y.Z` → CI builds the sdist
and wheel and attaches them to the GitHub Release. PyPI is not used.

## License

MIT — see `LICENSE`.
