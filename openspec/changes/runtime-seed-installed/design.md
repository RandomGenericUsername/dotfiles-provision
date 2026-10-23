# Design — seed the installed runtime

## D1. The seed is a consumer, not a source build

`runtime-seed` runs after `cli_tools`; the pinned runtime is already installed from
`<install>/cli-tools/dotfiles-runtime/<tag>/` into the uv tool bin dir. The seed must spawn that
binary, exactly like `runtime_daemon` / `runtime_clipboard` units do. Building it from a
composition source tree was the pre-extraction shape; after REQ-002 there is no such tree.

## D2. Resolve the bin dir the way uv does

`runtime_seed_bin_dir` uses the same expression as `cli_tools_bin_dir` and
`runtime_daemon_bin_dir`:

```jinja
{{ ansible_facts.env.UV_TOOL_BIN_DIR
   | default(ansible_facts.env.XDG_BIN_HOME | default(ansible_facts.env.HOME + '/.local/bin', true), true) }}
```

This keeps the seed pointed at the binary provisioning actually installed, including custom
`UV_TOOL_BIN_DIR` / `XDG_BIN_HOME` layouts.

## D3. Keep the seed check-gated and ordering unchanged

The task remains `when: not ansible_check_mode`; `bootstrap.yaml` keeps `runtime-seed` after
`config_links` and before `display-manager`/`verify`. Only the executable/path changes.

## Verification plan

| Claim | Command | Expected |
| --- | --- | --- |
| No composition source path | `rg -n 'src/runtime' ansible/playbooks/runtime-seed.yaml` | exit 1 |
| Installed binary argv | `uv run pytest -q tests/unit/test_runtime_seed_playbook.py` | exit 0 |
| Full engine gates | `make gates` | exit 0 |
| Release | `gh release view v0.1.8 --json assets` | wheel + sdist |
