---
id: REQ-010
title: "Support tpr as a palette producer (pin + roles + verify)"
kind: requirement
status: in-progress
lane: 3
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-010/
branch: ticket/REQ-010-tpr-producer-support
---

# Support tpr as a palette producer (pin + roles + verify)

## Requirement

Add `tpr` (theme-producer v0.1.0) to the provisioning engine as a second palette
producer, behind the existing CSG default. The engine must pin the CLI and its
three images, render its settings, deploy its templates, verify it, and expose
the runtime producer switch.

Scope:

- `cli_tools`: add `tpr` to the manifest mirror and the test fixture manifest;
  build `tpr-base-*`, `tpr-matugen-*`, `tpr-native-*` at the pin; install the
  `tpr` console script. The tpr install takes the tag from
  `THEME__CONTAINER__IMAGE_TAG` (no `--image-tag`), so the build loop must carry
  a per-tool tag env key.
- `settings`: `tpr-settings.toml.j2` (`engine = "native"`, `runtime.mode =
  "container"`, `image_prefix = "tpr"`, `image_tag = {{ settings_tpr_image_tag }}`,
  timeout 300, memory 512m); `settings_tpr_image_tag` mirror; a `settings_files`
  entry; `config_links` manages `theme-producer` (XDG config link).
- `assets`: copy the pinned tpr template catalog to
  `config/theme-producer/templates` (the path the runtime's `TprAdapter` reads);
  add the pin mirror and the missing-dir assert.
- `verify`: `verify_tpr_version` (v0.1.0), checkout/pin, the three images, the
  `tpr` console script, the settings file, the templates dir, and contract
  `0.4.0`.
- Runtime producer switch: a `runtime_palette_producer` var, default `csg`, written
  where the desktop session and the daemon see it (environment.d and/or the
  daemon unit), so activation is one explicit change, not an implicit one.
- Bump the engine to v0.1.21 and record the release.

Out of scope: dotfiles-v3 manifests/pins, the default producer flip, AGS/ITR,
and any tpr code change.

## Acceptance

- [ ] The manifest mirror, fixture manifest and `cli_tools` vars agree; tpr is
  installed and its three images are built at the pin with
  `THEME__CONTAINER__IMAGE_TAG`.
- [ ] `tpr-settings.toml.j2` renders the native engine, container mode, `tpr`
  prefix and the pin; the settings mirror and verify version agree.
- [ ] The tpr templates land in `config/theme-producer/templates`; a missing
  pinned checkout fails loud.
- [ ] `theme-producer` is a managed XDG config link.
- [ ] `verify` names the tpr version, checkout, pin, three images, console
  script, settings and templates; contract `0.4.0`.
- [ ] `runtime_palette_producer` defaults to `csg`; a single documented switch
  selects `tpr` for both the session CLI and the daemon.
- [ ] `make gates` green; engine v0.1.21 built/tagged.
