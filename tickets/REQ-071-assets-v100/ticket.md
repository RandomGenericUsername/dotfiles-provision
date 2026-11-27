---
id: REQ-071
title: "Mirror dotfiles-assets v1.0.0 (icons schema_major 2 corpus release)"
kind: requirement
status: done
lane: direct
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-071/
branch: ticket/REQ-071-assets-v100
---

# Mirror dotfiles-assets v1.0.0

The composition moved its `assets.tag` to `dotfiles-assets v1.0.0` (the
`schema_major 2` icons corpus release, REQ-149 in `dotfiles-assets`), and its
`make deploy-coverage` now fails because the engine mirror still says
`v0.22.6`:

```
FAIL: ansible/roles/assets/vars/main.yml: assets_pinned_tag 'v0.22.6' must mirror 'v1.0.0'
```

Mirror the corpus tag in every engine role var, the composition fixture, the
pin audit and the hardcoded assertions, then release the engine.

## Requirement

- Every `*_assets_pinned_tag` role mirror and the composition fixture
  (`assets.yaml`, `program-tuple.yaml`) name `v1.0.0`; the fixture's four
  checkout `source:` paths resolve under `assets/v1.0.0/`.
- `make gates-pin` is green (pin-audit, lint, docs-check, CI parity).
- The full release gates are green; the template-vars parity module executes
  with zero skips against the `v1.0.0` corpus.
- Release engine `v0.1.103`; the composition can pin it.

Out of scope: the `contracts` tuple pin (`v0.12.0`) is tracked separately from
the corpus tag and is not changed here.

## Acceptance

- [x] No active `v0.22.6` assets-pin mirror remains in `ansible/`, `tests/` or
      the CHANGELOG forward path.
- [x] `make gates-pin` exits 0.
- [x] `make gates` exits 0.
- [x] Template-vars parity executes against a clean `v1.0.0` archive with 0
      skips (10 passed). `make assets-parity` itself stays blocked at clone
      until the upstream `dotfiles-assets` tag is published — external, see
      Deviations.
- [x] Annotated tag `v0.1.103` created and `git describe --tags` reports it.

## Closure (2026-11-27)

- Released as `v0.1.103` (`62eddc5`); annotated tag `v0.1.103`,
  `git describe --tags` → `v0.1.103`.
- Pin-only gates (`make gates-pin`) RC 0: pin-audit PASS
  (`assets=v1.0.0, contracts=v0.12.0, platform=v1.2.0, apps=7, skins=5,
  targets=10, artifacts=2`), ruff clean, CI parity PASS, docs-check PASS.
- Full gates (`make gates`) RC 0: test `1113 passed, 35 skipped`; lint clean;
  hermetic `1110 passed, 38 skipped`; `uv lock --check` resolved.
- `make release-preflight TAG=v0.1.103` RC 0 (12 checks, no tag created).
- Local parity against a clean `git archive v1.0.0` corpus:
  `tests/unit/test_template_vars_parity.py` → `10 passed`, 0 skipped.

## Deviations

- `make assets-parity` fails closed at `git clone --branch v1.0.0`:
  `fatal: Remote branch v1.0.0 not found in upstream origin`. The
  `dotfiles-assets` `v1.0.0` tag exists locally but is not pushed
  (`git ls-remote --tags origin` lists `v0.22.6`, `v0.23.0` only). Publishing
  that tag is outside this repo's scope; once pushed the CI job should run the
  same 10 parity tests against the identical `templates/` class.
- The `contracts` tuple pin stays `v0.12.0`, while `dotfiles-assets v1.0.0`
  vendors contracts `v0.14.0` in its skin plane. A real provision of the
  `v1.0.0` skin plane therefore needs a separate contracts-tag bump; the engine
  mirror here only moves the corpus tag as requested.
