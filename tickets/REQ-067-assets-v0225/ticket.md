---
id: REQ-067
title: "Pin assets v0.22.5 (Wi-Fi + Bluetooth overlay skins)"
kind: requirement
status: done
lane: direct
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-067-assets-v0225/
branch: ticket/REQ-067-assets-v0225
---

# Pin assets v0.22.5

Mirror `dotfiles-assets v0.22.5` (approved Wi-Fi + Bluetooth overlay skins) in
every engine role and fixture. Move the composition fixture bar pin to
`v0.6.35`. Release the engine as `v0.1.99`.

## Closure (2026-11-25)

- Released as `v0.1.99` (`0cc1fd5`), tag pushed; tool reinstalled from the tag.
- Full gates RC 0: test 1113 passed / 35 skipped; hermetic 1110 passed / 38
  skipped; ruff and `uv lock --check` clean.
- Bar fixture moved to `v0.6.35`; assets mirror `v0.22.5`.
- Consumed by composition REQ-139 (`v0.2.12`).
