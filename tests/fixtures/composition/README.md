# Composition fixture (tests only)

This is a **test input**, not a deployable composition. It exists because the
engine repo (this repo) owns the Ansible tree but no composition checkout, while
several structural tests compare a role's mirror with the manifest that is
authoritative in the composition repo. `cli_tools` is different: it reads
`cli-tools.yaml` from here at run time (REQ-014), so this fixture is also the
role's input in tests.

Provenance: copied from `dotfiles-v3@854bac08` when the engine was extracted
(slice S6a):

- `dotfiles/provisioning/*.yaml` — the five manifests, byte-for-byte.
- `dotfiles/provisioning/scripts/gloview-activate` — byte-for-byte.

The runtime is **not** stubbed here: since REQ-002 it is the pinned
`dotfiles-runtime` repo, so the fixture carries only the composition files the
engine reads and compares against.

To check the engine against a **real** composition instead, point
`DOTFILES_COMPOSITION_ROOT` at one:

```bash
DOTFILES_COMPOSITION_ROOT=/home/inumaki/Development/dotfiles/dotfiles-v3 \
  uv run pytest tests/unit -q
```

CI runs against the fixture. A drift between the fixture and the live manifests
is a test-fixture refresh, not a role change; the composition's own gates remain
authoritative for the manifests themselves.
