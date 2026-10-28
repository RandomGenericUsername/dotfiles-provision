# dotfiles-provision

The provisioning **engine** for the dotfiles system: a hexagonal Python orchestrator
(`plan` / `apply` / `verify` / `bootstrap`) over an Ansible tree that establishes the machine
state the runtime assumes exists — packages, CLI tools, pinned assets, filesystem spine, rendered
settings and the desktop session.

**Charter — the engine, not the composition.** This repo owns `ansible/` and
`src/provisioning/`. The composition repo (`dotfiles-v3`) owns the manifests
(`dotfiles/provisioning/*.yaml`) and the provisioning scripts; the runtime is its own pinned
repo (`dotfiles-runtime`). The btop active-theme preference is host state in the install spine
(written by the studio, read by `btop_config`). The engine never ships or edits composition files; it reads them through the CLI
seam below.

**Workspace.** The engine is developed beside its consumers under `~/Development/dotfiles/`
(`dotfiles-v3`, `dotfiles-assets`, `ags-apps`, `ags-platform`, `contracts`, …). The canonical
ownership/pin map is [`../dotfiles-v3/docs/WORKSPACE.md`](../dotfiles-v3/docs/WORKSPACE.md);
the engine's own consumers pin it by tag.

## The composition seam (AD-17)

A pinned engine checkout has **no composition ancestors**, so no role derives a composition path
from `{{ playbook_dir }}`. The CLI resolves the paths once and passes them to Ansible as
extra-vars:

| Flag | Default | Extra-var | Used for |
| --- | --- | --- | --- |
| `--manifests-dir` | `<cwd>/dotfiles/provisioning` | `manifests_dir` | manifest validation, `scripts/gloview-activate` |
| `--composition-root` | parent of `--manifests-dir`'s parent | `composition_root` | the composition checkout root (`dotfiles/`); the legacy active-theme path is read only for the R-07 migration |
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

## Palette producer switch (REQ-010)

The runtime composes either the existing `csg` producer (default) or the opt-in
`theme-producer` (`tpr`) producer. `tpr` is pinned and verified either way; activation is
**one variable change**, never a separate provisioning path:

```bash
# csg is the shipped default; choose tpr for both the session CLI and the daemon:
dotfiles-provision apply -e runtime_palette_producer=tpr
# or export RUNTIME_PALETTE_PRODUCER=tpr for the run
```

The `runtime_daemon` role writes the value to
`~/.config/environment.d/10-dotfiles-runtime.conf` (the systemd user session environment the
AGS wallpaper selector inherits) and to the daemon unit's
`Environment="RUNTIME__PALETTE__PRODUCER=…"` line. The two cannot diverge because both render
from `runtime_palette_producer` (shipped default `csg`; `csg|tpr` is asserted).

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
dotfiles-provision = { git = "https://github.com/RandomGenericUsername/dotfiles-provision", tag = "v0.1.11" }
```

A tag is never moved or deleted; a fix ships as a new tag. The `cli-output` dependency is pinned
the same way in this repo's `pyproject.toml`.

**The wheel is self-contained.** The Ansible tree ships as package data
(`provisioning/_ansible`, via the wheel `force-include` in `pyproject.toml`), and the CLI resolves
it through `importlib.resources` — a `uv tool install git+…@<tag>` has no checkout beside
site-packages. Child `ansible`/`ansible-playbook` lookups prepend the interpreter's bin dir, so
the tool also runs without ansible-core's scripts installed globally. A source/editable checkout
still resolves the repo-root `ansible/`:

```bash
uv tool install "git+https://github.com/RandomGenericUsername/dotfiles-provision@v0.1.11"
dotfiles-provision --manifests-dir /path/to/dotfiles-v3/dotfiles/provisioning \
  --composition-root /path/to/dotfiles-v3 manifests
```

## Tests

- The fast suite (`make test`) is hermetic: manifests resolve through `tests/support.py` to
  `tests/fixtures/composition/` (a byte-copied composition subset), or to
  `$DOTFILES_COMPOSITION_ROOT` when set to a real checkout.
- `tests/unit/test_composition_seam.py` is the executable form of AD-17: an external
  `--manifests-dir` resolves every manifest, bad paths fail loud, and no YAML value or Jinja
  template under `ansible/` derives a path from `playbook_dir`.
- `make test-integration` runs the real `ansible-playbook --check` matrix and the disposable
  container proof. The container proof skips loudly unless `$DOTFILES_COMPOSITION_ROOT` names a
  real composition checkout.
- `make hermetic` runs the same selection with empty `HOME`/`XDG_*` and a foreign cwd. Tests that
  need the pinned `dotfiles-assets` corpus (a separate repo) skip with their stated reason unless
  `$DOTFILES_ASSETS_REPO`, `$DOTFILES_ASSETS_TEMPLATES_DIR` or a provisioned spine provides it.
- `make assets-parity` clones `dotfiles-assets` at the tag the composition pins, exports the corpus
  env, and runs `tests/unit/test_template_vars_parity.py` — failing if any parity test skips
  (R-01). CI runs the same target as the `assets-parity` job.

## Verify the engine pin

`verify` accepts the composition's `installer.pin` as `--expected-engine-tag` (forwarded to the
`expected_engine_tag` extra-var). When set, it runs
`dotfiles-provision --output-format plain version` from the tool bin dir and fails if the installed
engine is not that tag (leading `v` normalized). The empty default keeps a hand-run verify against
a development checkout usable.

```bash
dotfiles-provision verify --expected-engine-tag v0.1.11
```

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
