---
id: REQ-009
title: "Consume csg v0.2.1 + runtime v0.2.3 in one pin release (engine v0.1.17)"
kind: requirement
status: in-progress
lane: 1
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-009/
branch: ticket/REQ-009-consume-csg-v021-runtime-v023
---

# REQ-009 — Consume csg v0.2.1 + runtime v0.2.3 in one pin release (engine v0.1.17)

> **Numbering note.** The requested number `REQ-008` is already occupied on
> `main` by `tickets/REQ-008-ags-app-install-topology/` (commit `552e306`,
> active worktree `.worktrees/REQ-008/`). To keep ticket IDs, worktrees and
> branches unique without disturbing that in-flight item, this release uses
> `REQ-009`. Evidence:
> `ls -d tickets/REQ-008-* .worktrees/REQ-008`;
> `git log --oneline -1 552e306`.
> Verify: same two commands from the repo root.

## Requirement

The engine SHALL consume two upstream tags in one bounded pin release and SHALL
release the result as engine `v0.1.17`. The two pin groups are independent;
neither adds an install pin to the composition.

- `color-scheme-generator` **v0.2.1** (BUG-001 stale-container sweep) — all
  five csg mirrors move `v0.2.0` → `v0.2.1`:
  `cli_tools` (`csg.tag`), the assets csg-template mirror
  (`assets_csg_pinned_tag`; the corpus tag stays `v0.6.1`), the settings
  rendered image tag (`settings_csg_image_tag`), `verify_csg_version`, and the
  fixture `cli-tools.yaml` `csg.tag` + `assets.yaml` csg source path.
  `verify_csg_contract_version` stays `0.2.0` (`csg --version` prints
  `0.2.1 contract 0.2.0`);
- `dotfiles-runtime` **v0.2.3** (BUG-005 optional intent root) — the runtime
  mirrors move `v0.2.2` → `v0.2.3` in `cli_tools`, `verify_runtime_version`,
  `verify_runtime_tool_version`, and the fixture `cli-tools.yaml`;
- a focused red/green guard fails at the old literals and passes at
  `v0.2.1`/`v0.2.3`; a cross-leg guard proves the five csg mirrors and the
  fixture source path agree;
- the engine version is `0.1.17` (`pyproject.toml`,
  `src/provisioning/__init__.py`, `uv.lock`) with a CHANGELOG entry covering
  both pins, and the annotated tag `v0.1.17` carries the sdist + wheel.

No assets-corpus/ags-apps/weg/itr/ags-platform pin moves. **No new runtime
install pin is added here**; the composition install pin remains in
`dotfiles-v3` (`PIN-0116`, after this release).

## Pin / source evidence

### color-scheme-generator v0.2.1 (BUG-001)

- Upstream annotated tag exists and resolves to the expected peeled commit:

  ```text
  $ git ls-remote --tags https://github.com/RandomGenericUsername/color-scheme-generator 'refs/tags/v0.2*'
  0168c1bdad71876c11156aa3eaf19e2d4c80968e	refs/tags/v0.2.0
  9e23232d59480eaa0f4b65dedd7d8a4c194ab103	refs/tags/v0.2.0^{}
  d60ac9ec03b0bb7e92ca8c0b87a560a5b3d580fe	refs/tags/v0.2.1
  a6fdc7f4bde3c2e09f02e3fad7fa629a270c1315	refs/tags/v0.2.1^{}
  ```

  Annotated tag object `d60ac9e`; peeled commit `a6fdc7f`. Evidence: command
  output above.
  Verify: `git ls-remote --tags https://github.com/RandomGenericUsername/color-scheme-generator 'refs/tags/v0.2*'`.

- Upstream release metadata, both assets uploaded:

  ```text
  $ gh release view v0.2.1 --repo RandomGenericUsername/color-scheme-generator --json tagName,url,assets
  {"assets":[
    {"name":"color_scheme_generator-0.2.1-py3-none-any.whl","size":79815,"state":"uploaded"},
    {"name":"color_scheme_generator-0.2.1.tar.gz","size":136394,"state":"uploaded"}],
   "tagName":"v0.2.1",
   "url":"https://github.com/RandomGenericUsername/color-scheme-generator/releases/tag/v0.2.1"}
  ```

  Evidence: quoted `gh` output (asset URLs/ids elided for length; sizes and
  `state: uploaded` are verbatim).
  Verify: `gh release view v0.2.1 --repo RandomGenericUsername/color-scheme-generator --json tagName,url,assets`.

- The consumed behavior is recorded in the upstream changelog at the tag:

  ```text
  $ git -C /home/inumaki/Development/dotfiles/color-scheme-generator show v0.2.1:CHANGELOG.md | sed -n '25,48p'
  ## [0.2.1] - 2026-10-26
  Patch release for BUG-001. Container-mode `generate` and `show` now label their wrappers as
  csg-owned and sweep stale csg wrappers at startup, so a host `SIGKILL` or power loss no longer
  leaves detached containers behind indefinitely. ...
  - Container-mode wrappers carry `csg.managed=true`, `csg.session=<uuid>`, ...
  - A best-effort sweep runs before image preflight. It removes previous-boot csg-labelled wrappers
    immediately, and same-boot wrappers only after their own timeout plus a 60 s grace. Young
    same-boot wrappers from a concurrent run, unlabelled/foreign containers, and wrappers with no
    parseable age are left untouched; list/inspect/remove failures are logged and never fail ...
  - Package version `0.2.0` → `0.2.1`; `csg --version` now prints `0.2.1 contract 0.2.0`.
  ```

  The tag commit is `a6fdc7f chore(release): cut csg 0.2.1`; the later
  `2b6996e` is post-tag archive/evidence on `main`, not part of the tag.
  Evidence: `git log --oneline v0.2.0..v0.2.1` ends at `a6fdc7f`.
  Verify: `git -C /home/inumaki/Development/dotfiles/color-scheme-generator show v0.2.1:CHANGELOG.md`.

### dotfiles-runtime v0.2.3 (BUG-005)

- Upstream annotated tag exists and resolves to the expected peeled commit:

  ```text
  $ git ls-remote --tags https://github.com/RandomGenericUsername/dotfiles-runtime 'refs/tags/v0.2*'
  64368a0ebe81d9dab50e57d35ad35dd181e8f725	refs/tags/v0.2.0
  376be9f7399961e27857e7bc6bb6f974e61faf58	refs/tags/v0.2.0^{}
  ff5971cf1da6ab8205ff55036d1026f452891a59	refs/tags/v0.2.1
  f1ea89d80d9eac824cf5ee6605bf9f163689ea26	refs/tags/v0.2.1^{}
  2ce4bd1872a26b60c9e41f7dcf5fe476cb8ee477	refs/tags/v0.2.2
  5fff96e7ce3c240e8b4aff2ab7097a68104fd529	refs/tags/v0.2.2^{}
  960257251af75964c34a825fa64fb4106836faba	refs/tags/v0.2.3
  d0e37e91c88371bdd442278408680cec0c334cf4	refs/tags/v0.2.3^{}
  ```

  Annotated tag object `9602572`; peeled commit `d0e37e9`. Evidence: command
  output above.
  Verify: `git ls-remote --tags https://github.com/RandomGenericUsername/dotfiles-runtime 'refs/tags/v0.2*'`.

- Upstream release metadata, both assets uploaded:

  ```text
  $ gh release view v0.2.3 --repo RandomGenericUsername/dotfiles-runtime --json tagName,url,assets
  {"assets":[
    {"name":"dotfiles_runtime-0.2.3-py3-none-any.whl","size":355697,"state":"uploaded"},
    {"name":"dotfiles_runtime-0.2.3.tar.gz","size":639246,"state":"uploaded"}],
   "tagName":"v0.2.3",
   "url":"https://github.com/RandomGenericUsername/dotfiles-runtime/releases/tag/v0.2.3"}
  ```

  Evidence: quoted `gh` output (asset URLs/ids elided; sizes and
  `state: uploaded` verbatim).
  Verify: `gh release view v0.2.3 --repo RandomGenericUsername/dotfiles-runtime --json tagName,url,assets`.

- The consumed behavior is recorded in the upstream changelog at the tag:

  ```text
  $ git -C /home/inumaki/Development/dotfiles/dotfiles-runtime show v0.2.3:CHANGELOG.md | sed -n '1,22p'
  ## 0.2.3
  An absent optional intent root is informational, not degraded watch health (BUG-005).
  - The optional `$XDG_CONFIG_HOME/dotfiles/desired.json` root carries explicit optional metadata:
    an absent file or absent parent directory is reported as `optional_absent`, logged at INFO,
    and does not degrade watch health. Only a required-root failure sets
    `failed_roots`/`degraded`.
  - `watch-health.json` gains the additive `optional_absent` field under the unchanged
    `version: 1`; ...
  - `inspect daemon` and `doctor` include `optional_absent` in JSON and print
    `OPTIONAL (absent, not watched) <path>` ... while keeping exit 0; ...
  - `WatchCoordinator` retries once per burst when an optional root is absent, ...
  ```

  The post-release evidence commit is `bb3cbb4` (`docs(BUG-005): record the
  v0.2.3 tag and release evidence`), after the tag target `d0e37e9`.
  Evidence: `git -C dotfiles-runtime log --oneline -3`.
  Verify: `git -C /home/inumaki/Development/dotfiles/dotfiles-runtime show v0.2.3:CHANGELOG.md`.

### Current engine pins (old literals)

```text
$ rg -n 'tag: v0\.2\.[0-9]|csg_pinned_tag: v0\.2\.[0-9]|csg_image_tag: v0\.2\.[0-9]|verify_(csg|runtime)_(version|tool_version): v?0\.2\.[0-9]|cli-tools/csg/v0\.2\.[0-9]' ansible/roles/... tests/fixtures/...
ansible/roles/cli_tools/vars/main.yml:121:    tag: v0.2.0        # csg
ansible/roles/cli_tools/vars/main.yml:124:    tag: v0.2.0        # weg (stays)
ansible/roles/cli_tools/vars/main.yml:127:    tag: v0.2.0        # itr (stays)
ansible/roles/cli_tools/vars/main.yml:130:    tag: v0.2.2        # dotfiles-runtime
ansible/roles/assets/vars/main.yml:104:assets_csg_pinned_tag: v0.2.0
ansible/roles/settings/vars/main.yml:93:settings_weg_image_tag: v0.2.0   # stays
ansible/roles/settings/vars/main.yml:105:settings_csg_image_tag: v0.2.0
ansible/roles/verify/vars/main.yml:336:verify_runtime_version: v0.2.2
ansible/roles/verify/vars/main.yml:337:verify_runtime_tool_version: 0.2.2
ansible/roles/verify/vars/main.yml:367:verify_csg_version: v0.2.0
tests/fixtures/composition/dotfiles/provisioning/cli-tools.yaml:13:    tag: v0.2.0   # csg
tests/fixtures/composition/dotfiles/provisioning/cli-tools.yaml:16:    tag: v0.2.0   # weg (stays)
tests/fixtures/composition/dotfiles/provisioning/cli-tools.yaml:19:    tag: v0.2.0   # itr (stays)
tests/fixtures/composition/dotfiles/provisioning/cli-tools.yaml:22:    tag: v0.2.2   # dotfiles-runtime
tests/fixtures/composition/dotfiles/provisioning/assets.yaml:47: source .../cli-tools/csg/v0.2.0/src/...
```

The fixture corpus pin `assets.tag` is `v0.6.1` and does not move. Evidence:
the modified-line comments above reflect the named entries; the raw command
output is in the Closeout red row.
Verify: rerun the `rg` command from the repo root.

### Scope note — engine-side mirror vs composition install pin

`cli_tools` and `verify` carry hand-maintained literals; `assets`,
`settings`, `verify` and the fixture are parity-locked by the existing
`test_assets_role`/`test_settings_role`/`test_verify_role` guards. Leaving any
csg/runtime leg at the old tag makes `make gates` red or the final `verify`
unsatisfiable. The real composition manifests
(`dotfiles-v3/dotfiles/provisioning/*.yaml`) are untouched — that is
`PIN-0116`'s change.

## Triage

- `kind: requirement` — consume two upstream releases in one bounded pin
  release; no defect repro fields apply.
- `lane: 1` — XS direct: five csg literals, three runtime literals, one fixture
  pair, existing parity/execution tests, CHANGELOG, engine version, standard
  release procedure. No OpenSpec capability delta (`links.openspec: none`).
- Numbering deviation recorded above: `REQ-008` is the in-flight AGS topology
  item, so this ticket is `REQ-009`.

Evidence: this ticket + the pin inventory above.
Verify: `rg -n '^kind: requirement|^lane: 1' tickets/REQ-009-consume-csg-v021-runtime-v023/ticket.md`.

## Acceptance

- [ ] A focused red guard fails at `v0.2.0`/`v0.2.2` and passes at
      `v0.2.1`/`v0.2.3`; the red and green outputs are recorded below.
- [ ] All five csg mirrors are `v0.2.1`: `cli_tools` `csg.tag`,
      `assets_csg_pinned_tag`, `settings_csg_image_tag`, `verify_csg_version`,
      fixture `cli-tools.yaml` `csg.tag`; the fixture `assets.yaml` csg source
      path is `v0.2.1`; `verify_csg_contract_version` stays `0.2.0`;
      `assets.tag` stays `v0.6.1`.
- [ ] The `cli_tools` runtime tag, `verify_runtime_version: v0.2.3`,
      `verify_runtime_tool_version: 0.2.3`, and the fixture runtime tag are
      `v0.2.3`; existing literal assertions are updated.
- [ ] weg/itr stay `v0.2.0`; `settings_weg_image_tag` and both `verify_weg_*`
      image/version legs stay `v0.2.0`; all `verify_*_contract_version`
      values stay `0.2.0`; no assets/ags-apps/ags-platform pin moves.
- [ ] Engine version `0.1.17` (`pyproject.toml`,
      `src/provisioning/__init__.py`, `uv.lock`) and a CHANGELOG entry covering
      both pins.
- [ ] `make gates`, `make test-integration`, `make assets-parity` (at
      `v0.6.1`), `make build`, `uv run dotfiles-provision version`, and the
      wheel-contents check are green.
- [ ] Merged to `main`; annotated tag `v0.1.17`; tag CI all green; GitHub
      Release carries the wheel and sdist; branch/tag pushed.
- [ ] Post-tag engine checkout inspection confirms exactly the csg/runtime
      legs changed.

## Out of scope

- `dotfiles-v3` (`PIN-0116`: `cli-tools.yaml`, `installer.pin`, docs) — next
  orchestrator step, separate repo.
- Host provisioning/reboot and live verification (user-run, sudo), after
  `PIN-0116`.
- Upstream internals: both fixes ship in csg `v0.2.1` and runtime `v0.2.3`.

## Closeout

| Claim | Command | Result |
| --- | --- | --- |
| Red (old pins) | pending | pending |
| Green (new pins) | pending | pending |
| Engine gates | pending | pending |
| Integration | pending | pending |
| Assets parity | pending | pending |
| Build / version | pending | pending |
| Pin scope | pending | pending |
| Merge / tag / release | pending | pending |

Evidence: pending.
Verify: pending.

### User host steps (sudo; user-run — the agent must not provision/reboot)

1. In `dotfiles-v3`, land `PIN-0116`:
   - `dotfiles/provisioning/cli-tools.yaml`: `csg` tag **v0.2.1** and
     `dotfiles-runtime` tag **v0.2.3**;
   - `dotfiles/provisioning/installer.pin`: **v0.1.17**;
   - docs/CHANGELOG; `make gates-ci` + `make deploy-coverage`.
2. Run the host provision with sudo, then reboot.
3. Verify:
   `make provision ARGS="--output-format plain verify --expected-engine-tag v0.1.17"`.
