# Composition fixture (tests only)

This is a **test input**, not a deployable composition. It exists because the
engine repo (this repo) owns the Ansible tree but no composition checkout, while
several structural tests have to compare a role's mirror with the manifest that
is authoritative in the composition repo.

Provenance: copied from `dotfiles-v3@854bac08` when the engine was extracted
(slice S6a):

- `dotfiles/provisioning/*.yaml` — the five manifests, byte-for-byte.
- `dotfiles/provisioning/scripts/gloview-activate` — byte-for-byte.
- `dotfiles/config/btop/active-theme` — byte-for-byte.
- `src/runtime/pyproject.toml` — a minimal stub: the real runtime lives in the
  composition; the engine only needs the path to exist for the seam test.

To check the engine's mirrors against a **real** composition instead, point
`DOTFILES_COMPOSITION_ROOT` at one:

```bash
DOTFILES_COMPOSITION_ROOT=/home/inumaki/Development/dotfiles/dotfiles-v3 \
  uv run pytest tests/unit -q
```

CI runs against the fixture. A drift between the fixture and the live manifests
is a test-fixture refresh, not a role change; the composition's own gates remain
authoritative for the manifests themselves.
