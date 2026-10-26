---
id: REQ-007
title: "Consume assets v0.6.1 + runtime v0.2.2 in one pin release (engine v0.1.16)"
kind: requirement
status: in-progress
lane: 1
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-007/
branch: ticket/REQ-007-consume-assets-v061-runtime-v022
---

# REQ-007 — Consume assets v0.6.1 + runtime v0.2.2 in one pin release (engine v0.1.16)

## Requirement

The engine SHALL consume two upstream tags in one bounded pin release and SHALL
release the result as engine `v0.1.16`:

- `dotfiles-assets` **v0.6.1** (wlogout Logout action `uwsm stop`, BUG-001) —
  **every** `*_assets_pinned_tag` mirror moves `v0.6.0` → `v0.6.1`, and the
  fixture composition manifest (`assets.tag` + its three checkout sources)
  moves in lockstep;
- `dotfiles-runtime` **v0.2.2** (BUG-003 icon-contrast parser + retained
  BUG-004 btop-studio skip) — the engine-side runtime mirror moves
  `v0.2.0` → `v0.2.2` in `cli_tools`, `verify_runtime_version`,
  `verify_runtime_tool_version`, and the fixture `cli-tools.yaml`;
- the red version/parity guard fails at `v0.6.0`/`v0.2.0` and passes at
  `v0.6.1`/`v0.2.2`;
- the engine version is `0.1.16` (`pyproject.toml`,
  `src/provisioning/__init__.py`, `uv.lock`) with a CHANGELOG entry covering
  both pins and the wlogout logout fix;
- annotated tag `v0.1.16` and a GitHub Release carrying the sdist and wheel.

No ags-apps/csg/weg/itr/ags-platform pin moves. **No new runtime install pin is
added here**; the actual composition install pin remains in `dotfiles-v3`
(`PIN-0115`, next orchestrator step).

## Pin / source evidence

### dotfiles-assets v0.6.1 (wlogout logout)

- Upstream annotated tag exists and resolves to the expected peeled commit:

  ```text
  $ git ls-remote --tags https://github.com/RandomGenericUsername/dotfiles-assets 'refs/tags/v0.6.1*'
  b2ad3a90953633602ec6a04e564f6f98ae11ce2a	refs/tags/v0.6.1
  f8cc8288eebeab1f0759d6dec05b978b662ae19e	refs/tags/v0.6.1^{}
  ```

  The peeled commit `f8cc828` is the expected target (annotated tag object
  `b2ad3a9`). Evidence: command output above.
  Verify: `git ls-remote --tags https://github.com/RandomGenericUsername/dotfiles-assets 'refs/tags/v0.6.1*'`.

- Upstream release metadata:

  ```text
  $ gh release view v0.6.1 --repo RandomGenericUsername/dotfiles-assets \
      --json tagName,name,publishedAt,url,assets
  {"assets":[],
   "name":"v0.6.1 — wlogout Logout uses uwsm stop",
   "publishedAt":"2026-10-26T21:20:06Z",
   "tagName":"v0.6.1",
   "url":"https://github.com/RandomGenericUsername/dotfiles-assets/releases/tag/v0.6.1"}
  ```

  `assets` is empty because this repo ships no build artifacts; the tag + notes
  are the release. Evidence: quoted `gh` output; URL above.
  Verify: `gh release view v0.6.1 --repo RandomGenericUsername/dotfiles-assets --json tagName,name,url`.

- The consumed change is the one-line wlogout Logout action, guarded upstream
  by `make validate-configs`:

  ```text
  $ git -C dotfiles-assets diff v0.6.0..v0.6.1 -- configs/wlogout/layout
  -    "action" : "loginctl terminate-user $USER",
  +    "action" : "uwsm stop",
  ```

  Upstream commits: `19e82f6` (fix), `9acadc3` (pin the logout action in
  `validate-configs`), `f8cc828` (release notes / tag target). Evidence:
  command output above.
  Verify: `git -C /home/inumaki/Development/dotfiles/dotfiles-assets diff v0.6.0..v0.6.1 -- configs/wlogout/layout`.

### dotfiles-runtime v0.2.2 (BUG-003 + retained BUG-004)

- Upstream annotated tag exists and resolves to the expected peeled commit:

  ```text
  $ git ls-remote --tags https://github.com/RandomGenericUsername/dotfiles-runtime 'refs/tags/v0.2.2*'
  2ce4bd1872a26b60c9e41f7dcf5fe476cb8ee477	refs/tags/v0.2.2
  5fff96e7ce3c240e8b4aff2ab7097a68104fd529	refs/tags/v0.2.2^{}
  ```

  The peeled commit `5fff96e` is the expected target (annotated tag object
  `2ce4bd1`). Evidence: command output above.
  Verify: `git ls-remote --tags https://github.com/RandomGenericUsername/dotfiles-runtime 'refs/tags/v0.2.2*'`.

- Upstream release metadata (sdist/wheel present):

  ```text
  $ gh release view v0.2.2 --repo RandomGenericUsername/dotfiles-runtime \
      --json tagName,name,publishedAt,url,assets
  {"assets":["dotfiles_runtime-0.2.2-py3-none-any.whl",
             "dotfiles_runtime-0.2.2.tar.gz"],
   "name":"v0.2.2",
   "publishedAt":"2026-10-26T21:19:51Z",
   "tagName":"v0.2.2",
   "url":"https://github.com/RandomGenericUsername/dotfiles-runtime/releases/tag/v0.2.2"}
  ```

  Evidence: quoted `gh` output; URL above.
  Verify: `gh release view v0.2.2 --repo RandomGenericUsername/dotfiles-runtime --json tagName,name,url,assets`.

- Upstream `CHANGELOG.md` at `v0.2.2` records the consumed behavior:

  ```text
  ## 0.2.2
  The icon-contrast prefs reader accepts its own canonical document at any entry
  count (BUG-003).
  ...
  - BUG-004's btop-theme-studio skip is retained: a wallpaper change leaves the
    studio running so unsaved edits are not lost.
  - Includes BUG-002 (csg timeout/cleanup), released in v0.2.1; no further
    changes to it in this release.
  ```

  Evidence: `git -C dotfiles-runtime show v0.2.2:CHANGELOG.md`.
  Verify: same command.

### Current engine pins (all `v0.6.0` / `v0.2.0`)

```text
$ rg -n 'assets_pinned_tag: v0\.6\.0' ansible/roles/*/vars/main.yml
ansible/roles/assets/vars/main.yml:19:assets_pinned_tag: v0.6.0
ansible/roles/btop_config/vars/main.yml:78:btop_config_assets_pinned_tag: v0.6.0
ansible/roles/compositor_configs/vars/main.yml:46:compositor_configs_assets_pinned_tag: v0.6.0
ansible/roles/config_copies/vars/main.yml:58:config_copies_assets_pinned_tag: v0.6.0
ansible/roles/display_manager/vars/main.yml:37:display_manager_assets_pinned_tag: v0.6.0
ansible/roles/kitty_config/vars/main.yml:30:kitty_config_assets_pinned_tag: v0.6.0
ansible/roles/verify/vars/main.yml:167:verify_assets_pinned_tag: v0.6.0
ansible/roles/wlogout_config/vars/main.yml:12:wlogout_config_assets_pinned_tag: v0.6.0
ansible/roles/zsh_config/vars/main.yml:36:zsh_config_assets_pinned_tag: v0.6.0

$ rg -n 'verify_runtime_version: v0\.2\.0|verify_runtime_tool_version: 0\.2\.0' ansible/roles/verify/vars/main.yml
ansible/roles/verify/vars/main.yml:336:verify_runtime_version: v0.2.0
ansible/roles/verify/vars/main.yml:337:verify_runtime_tool_version: 0.2.0

$ rg -n -A2 'name: dotfiles-runtime' ansible/roles/cli_tools/vars/main.yml tests/fixtures/composition/dotfiles/provisioning/cli-tools.yaml
ansible/roles/cli_tools/vars/main.yml:128:  - name: dotfiles-runtime
ansible/roles/cli_tools/vars/main.yml:130:    tag: v0.2.0
tests/fixtures/composition/dotfiles/provisioning/cli-tools.yaml:20:  - name: dotfiles-runtime
tests/fixtures/composition/dotfiles/provisioning/cli-tools.yaml:22:    tag: v0.2.0
```

The fixture assets manifest also pins `assets.tag: v0.6.0` and repeats that tag
in three checkout sources:
`tests/fixtures/composition/dotfiles/provisioning/assets.yaml:20,31,34,37`.

Evidence: the `rg` output above plus the test `rg` below.
Verify: rerun the three commands.

### Scope note — engine-side mirror vs composition install pin

The engine's `cli_tools` role and `verify` are hand-mirrored literals; the
fixture manifest is parity-locked by `test_cli_tools_parity_with_manifest` and
`TestVerifyRuntimePinMirror`. Leaving any leg at `v0.2.0` makes `make gates`
red or the final `verify` unsatisfiable (it would demand a version the engine
never installs). The engine-side literals therefore move together; **no new pin
location is added**, and the real composition manifest
(`dotfiles-v3/dotfiles/provisioning/cli-tools.yaml`) is untouched — that is
`PIN-0115`'s change.

## Triage

Per `.opencode/commands/triage.md`:

- `kind: requirement` — the request is "consume two upstream releases in one
  bounded pin release", not a defect in this repo and not an epic. No
  `repro:`/`observed:`/`expected:` bug fields apply. Evidence: this ticket.
  Verify: `rg -n '^kind: requirement' tickets/REQ-007-consume-assets-v061-runtime-v022/ticket.md`.
- `lane: 1` — XS direct. Fully understood: 9 literal assets mirrors, 3 runtime
  literals, one fixture manifest pair, the existing parity/execution tests,
  CHANGELOG, engine version, and the standard README release procedure. Both
  upstream behavior changes ship in their own repos; this repo has no OpenSpec
  capability delta (`links.openspec: none`).
- No ambiguity to resolve; BMAD is not invoked.

Evidence: the pin inventory above + `rg -n '^kind: requirement|^lane: 1'
tickets/REQ-007-consume-assets-v061-runtime-v022/ticket.md`.
Verify: same `rg`.

## Acceptance

- [ ] A red version/parity guard fails at `v0.6.0`/`v0.2.0` and passes at
      `v0.6.1`/`v0.2.2`.
- [ ] Every `*_assets_pinned_tag` mirror is `v0.6.1` (assets, btop_config,
      compositor_configs, config_copies, display_manager, kitty_config, verify,
      wlogout_config, zsh_config); the fixture `assets.yaml` tag and its three
      checkout sources are `v0.6.1`.
- [ ] The `cli_tools` runtime tag, `verify_runtime_version: v0.2.2`,
      `verify_runtime_tool_version: 0.2.2`, and the fixture `cli-tools.yaml`
      runtime tag are `v0.2.2`; existing literal assertions updated.
- [ ] Engine version `0.1.16` (`pyproject.toml`,
      `src/provisioning/__init__.py`, `uv.lock`) and a CHANGELOG entry covering
      both pins and the wlogout Logout fix.
- [ ] `make gates` green in the worktree; `make assets-parity` green at
      `v0.6.1`; `make test-integration` recorded (run or explicitly not
      required by the release procedure).
- [ ] Merged to `main`; annotated tag `v0.1.16`; GitHub Release carries the
      sdist and wheel; branch/tag pushed.
- [ ] ags-apps (`v0.4.3`), csg/weg/itr and ags-platform (`v0.2.0`) pins
      unchanged; no runtime install pin added in this repo.

## Out of scope

- `dotfiles-v3` (`PIN-0115`: `assets.yaml`, `cli-tools.yaml`,
  `installer.pin`, docs/CHANGELOG) — next orchestrator step, separate repo.
- Host provisioning/reboot and the host logout/5-login acceptance (user-run,
  sudo; the VM matrix was waived by the user).
- Upstream internals: both fixes ship in `dotfiles-assets` v0.6.1 and
  `dotfiles-runtime` v0.2.2.

## Closeout

| Claim | Command | Result |
| --- | --- | --- |
| Red (old pins) | pending | pending |
| Green (new pins) | pending | pending |
| Related tests | pending | pending |
| Engine gates | pending | pending |
| Assets parity | pending | pending |
| Integration | pending | pending |
| Pin scope | pending | pending |
| Engine version | pending | pending |
| Merge | pending | pending |
| Tag | pending | pending |
| Tag CI | pending | pending |
| Release assets | pending | pending |
| Release URL | pending | pending |

Evidence: filled after the implementation/gates run.
Verify: rerun the red/green commands and `make gates` from
`.worktrees/REQ-007/`.

### User host steps (sudo; user-run — the agent must not provision/reboot)

1. In `dotfiles-v3`, land `PIN-0115`:
   - `dotfiles/provisioning/assets.yaml`: `assets.tag` **v0.6.1** and the three
     `.../assets/<tag>/...` sources **v0.6.1**;
   - `dotfiles/provisioning/cli-tools.yaml`: `dotfiles-runtime` tag **v0.2.2**;
   - `dotfiles/provisioning/installer.pin`: **v0.1.16**;
   - docs/CHANGELOG at **0.6.7**; `make gates-ci` + `make deploy-coverage`.
2. Run the host provision with sudo (`./bootstrap.sh` or
   `make bootstrap ARGS="--ask-become-pass"`), then reboot.
3. Logout acceptance: click Logout → the Pixie greeter returns in <30 s; then
   5 logins >3 min and `python3 scripts/check-session-bounce.py --boot 0` → 0.
4. Verify: `make provision ARGS="--output-format plain verify --expected-engine-tag v0.1.16"`.
