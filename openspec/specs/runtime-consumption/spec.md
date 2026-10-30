# runtime-consumption Specification

## Purpose

This capability governs how the installer engine consumes `dotfiles-runtime` after its extraction:
as a pinned `{name, repo, tag}` CLI entry installed from a tag-bearing checkout, with `verify`
asserting the checkout, the `pinned` record and the installed version by execution. It exists so a
runtime pin bump is one manifest/role/verify edit and a wrong-tag install cannot hide behind a
green `command -v`.

## Requirements

### Requirement: the runtime is a pinned CLI entry

`roles/cli_tools` SHALL load `dotfiles-runtime` as `{name, repo, tag}` with no `source` key, like
`csg`/`weg`/`itr`, from `{{ cli_tools_manifests_dir }}/cli-tools.yaml` at run time, not from an
in-role pin list. It SHALL install it from `<install>/cli-tools/dotfiles-runtime/<tag>/`, record
the tag in `pinned` beside it, and publish `cli_tools_tags` (name → tag) for later plays.

Source: spine AD-10/AD-11; `dotfiles-v3/tickets`; REQ-014.

#### Scenario: the manifest is the pin source

- **WHEN** the composition manifest pins `dotfiles-runtime` at a different tag
- **THEN** `cli_tools` installs, records and image-tags that tag without an engine edit

#### Scenario: the source path selects nothing

- **WHEN** `cli_tools` is filtered to entries without `repo`
- **THEN** the result is empty, and the source-path install/upgrade loops are no-ops

#### Scenario: the pinned branch installs the runtime

- **WHEN** the `cli_tools` role runs against the manifest entry
- **THEN** it clones the runtime repo at the manifest tag, removes `.git`, writes `pinned`, and
  installs from the checkout (never a `git+…@tag` URL)

### Requirement: the CLI manifest is validated before install

`roles/cli_tools` SHALL validate `kind: cli-tools`, a non-empty `entries` list, unique safe names
(`^[a-z][a-z0-9-]*$`), exactly one addressing shape (`source` XOR `repo` + `tag`) and non-empty
values before any clone/install.

Source: REQ-014.

#### Scenario: a malformed manifest fails before install

- **WHEN** the manifest has the wrong kind, no entries, or an entry with a duplicate/unsafe name,
  both addressing shapes, or a missing/empty value
- **THEN** the role fails naming the offending entry and field before any clone/install

### Requirement: verify asserts the runtime pin by execution

`roles/verify/vars/main.yml` SHALL list `dotfiles-runtime` in `verify_cli_tools` and carry
`verify_runtime_version`, `verify_runtime_tool_version`, `verify_runtime_checkout` and
`verify_runtime_pin_file`. `verify` SHALL assert the checkout is a directory, the pin record is a
file containing exactly the tag, and `dotfiles-runtime version` exits 0 and prints the tool
version.

Source: spine AD-10/AD-11; `dotfiles-runtime` `version` command.

#### Scenario: a stale runtime install fails

- **WHEN** the installed runtime's checkout, pin record or version differs from the manifest pin
- **THEN** the verify assert fails naming the observed checkout/pin/stdout

#### Scenario: the runtime is on PATH

- **WHEN** `verify_cli_tools` is probed with the tool bin dir prepended
- **THEN** `dotfiles-runtime` resolves, alongside `csg`, `weg` and `itr`

### Requirement: the seed step runs the installed pinned runtime

`ansible/playbooks/runtime-seed.yaml` SHALL invoke the installed `dotfiles-runtime` binary from
`runtime_seed_bin_dir` (uv's tool bin dir). It SHALL NOT invoke
`uv run --directory {{ composition_root }}/src/runtime` or read any composition source path.

Source: `runtime-consumption`; REQ-002; BUG-001.

#### Scenario: the seed uses the installed binary

- **WHEN** the `runtime-seed` playbook is parsed
- **THEN** the wallpaper-set argv starts with
  `{{ runtime_seed_bin_dir }}/dotfiles-runtime`, and the task remains
  `when: not ansible_check_mode`

#### Scenario: no composition source path remains

- **WHEN** `rg -n 'src/runtime|uv run --directory' ansible/playbooks/runtime-seed.yaml` runs
- **THEN** it exits 1 with no matches
