# runtime-consumption (delta)

## ADDED Requirements

### Requirement: the runtime is a pinned CLI entry

`roles/cli_tools/vars/main.yml` SHALL mirror `dotfiles-runtime` as `{name, repo, tag}` with no
`source` key, like `csg`/`weg`/`itr`. The role SHALL install it from the tag-bearing checkout
`<install>/cli-tools/dotfiles-runtime/<tag>/` and record the tag in `pinned` beside it.

Source: spine AD-10/AD-11; `dotfiles-v3/tickets` / runtime repo `v0.1.0`.

#### Scenario: the source path selects nothing

- **WHEN** `cli_tools` is filtered to entries without `repo`
- **THEN** the result is empty, and the source-path install/upgrade loops are no-ops

#### Scenario: the pinned branch installs the runtime

- **WHEN** the `cli_tools` role runs against the mirrored entry
- **THEN** it clones the runtime repo at `v0.1.0`, removes `.git`, writes `pinned`, and installs
  from the checkout (never a `git+…@tag` URL)

### Requirement: verify asserts the runtime pin by execution

`roles/verify/vars/main.yml` SHALL list `dotfiles-runtime` in `verify_cli_tools` and carry
`verify_runtime_version`, `verify_runtime_tool_version`, `verify_runtime_checkout` and
`verify_runtime_pin_file`. `verify` SHALL assert the checkout is a directory, the pin record is a
file containing exactly the tag, and `dotfiles-runtime version` exits 0 and prints the tool
version.

Source: spine AD-10/AD-11; `dotfiles-runtime` `version` command.

#### Scenario: a stale runtime install fails

- **WHEN** the installed runtime's checkout, pin record or version differs from the mirror
- **THEN** the verify assert fails naming the observed checkout/pin/stdout

#### Scenario: the runtime is on PATH

- **WHEN** `verify_cli_tools` is probed with the tool bin dir prepended
- **THEN** `dotfiles-runtime` resolves, alongside `csg`, `weg` and `itr`
