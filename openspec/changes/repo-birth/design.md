# Design — repo birth and the composition seam

## Decisions

### D1. History is imported, the harness is the second commit

The provisioning tree has real history in `dotfiles-v3` (`src/provisioning/`, `ansible/`,
`tests/`). The split preserved it as the imported base; the public repo's `main` therefore starts
at the imported history and the mu harness seed lands on top as its own commit. A fresh-root
import would make the first commit unrelated to the code's history and lose the "why" of every
role.

Evidence: `main` = imported history + `chore: seed the mu harness byte-for-byte` (one commit
ahead of the imported base).
Verify: `git log --oneline -2`.

### D2. The composition seam is resolved once, in the CLI, and passed as extra-vars

A pinned engine checkout has no `dotfiles/provisioning/` above `ansible/`: the old
`{{ playbook_dir }}/../../../..` climbed out of the engine and resolved to a path that does not
exist. The engine now resolves a `CompositionSeam` once
(`src/provisioning/application/use_cases.py`):

- `--manifests-dir` defaults to `<cwd>/dotfiles/provisioning`;
- `--composition-root` defaults to the manifests dir's grandparent;
- both are resolved to absolute paths, validated before Ansible starts, and passed as the
  `manifests_dir` / `composition_root` extra-vars alongside `install_dir` / `os_family`.

Roles read those extra-vars (`cli_tools`, `btop_config`, `runtime-seed`) or no composition tree at
all (the pinned-asset roles). Direct `ansible-playbook` runs fail loud in the consuming role's
assert rather than silently reading the engine checkout.

Evidence: `tests/unit/test_composition_seam.py::TestExternalManifestsDir` resolves all five
manifests from the engine cwd; `TestNoRoleDerivesFromPlaybookDir` scans every YAML value and Jinja
template.
Verify: `uv run pytest -q tests/unit/test_composition_seam.py`.

### D3. Tests carry a fixture composition, never an absolute dotfiles path

Unit tests assert manifest parity (pins, entries, required vars). They cannot walk up to a
composition any more, so `tests/support.py` resolves:

1. `$DOTFILES_COMPOSITION_ROOT` — an explicit real checkout, for drift checks against live
   manifests;
2. `tests/fixtures/composition/` — five manifests, the gloview script, the btop active-theme and
   a runtime stub, byte-copied from `dotfiles-v3` at extraction time.

The fixture is a test input, never a deployed source. The integration container test needs the
real runtime and therefore skips unless `$DOTFILES_COMPOSITION_ROOT` names one.

Evidence: `diff` of each fixture manifest against `dotfiles-v3/dotfiles/provisioning/` is empty.
Verify: `diff -r <fixture manifests> /home/inumaki/Development/dotfiles/dotfiles-v3/dotfiles/provisioning`.

### D4. The Makefile's `GATES` is the single gate list; CI is compared to it

The workflow has one job per gate so a failure names the gate, but a hand-maintained job list
drifts. `scripts/ci-gates-parity.py` parses `GATES` from the `Makefile` and the job keys from the
workflow and fails on any unmatched entry in either direction. CI-only jobs (`ci-gates-parity`,
`release`) are declared with a reason; a stale declaration fails.

`test` is the fast suite (`-m "not integration and not container_target"`), because the
integration tests shell real `ansible-playbook` runs against the host/container and are a
developer proof, not a stock-runner gate. `make test-integration` keeps them one command away.

Evidence: `make ci-gates-parity` → `PASS gates=[...] jobs=[...] exempt=[...]`.
Verify: `make ci-gates-parity`.

### D5. Hermetic means hermetic, not "green on this host"

`make hermetic` runs the same suite with `HOME` and all four `XDG_*` roots pointed at fresh temp
dirs and an unrelated cwd. The suite already resolves answer paths explicitly (engine root via
`__file__`, composition via the fixture), so no host-provided spine can change the result.

Evidence: `make hermetic` runs from the repo root with a throwaway `HOME`.
Verify: `make hermetic` → exit 0, same test count as `make test`.

### D6. Release = annotated tag + artifacts; consumption = pinned checkout

The tag is the immutable release record and CI attaches the sdist and wheel built from that
commit. Those artifacts do not contain the Ansible tree (the wheel packages only
`src/provisioning`), so a consumer must install the engine from the pinned checkout, not from the
wheel. `README.md` states this explicitly rather than implying a self-contained package.

Evidence: `pyproject.toml` `[tool.hatch.build.targets.wheel] packages = ["src/provisioning"]`;
`_ANSIBLE_ROOT` resolves beside the engine checkout, not inside site-packages.
Verify: `uv build && unzip -l dist/dotfiles_provision-0.1.0-py3-none-any.whl | rg ansible` → no
matches.
