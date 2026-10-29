---
id: BUG-007
title: "tpr native engine is not provisioned: bootstrap is green, first tpr wallpaper set fails"
kind: bug
status: in-progress
lane: 2
severity: high
links:
  openspec: none
  bmad: none
worktree: .worktrees/REQ-013/
branch: ticket/REQ-013-bootstrap-producer-and-rofi
repro: "Bootstrap with RUNTIME_PALETTE_PRODUCER=tpr, then run `RUNTIME__PALETTE__PRODUCER=tpr RUNTIME__PALETTE__TPR_ENGINE=native dotfiles-runtime wallpaper set <image>` on the fresh host. It fails with EngineUnavailableError because tpr-native is not on PATH."
observed: "2026-10-29: after bootstrap, `tpr list-engines` reported native available=false; the first tpr set failed with `engine 'native' is not available on this host`; after manually installing the prebuilt theme-producer `native/target/release/tpr-native` (0.1.0) to ~/.local/bin, the same set succeeded and produced the tpr cache entry."
expected: "A bootstrap that selects tpr/native installs or otherwise provides a usable native engine, and `verify` fails if a selected producer cannot generate a palette."
---

# BUG-007 — tpr native engine is not provisioned

## Summary

The tpr runtime seam runs tpr in **local** mode and selects the **native**
engine. The native engine is a separate Rust helper, `tpr-native`, on `PATH`.
Provisioning installs the tpr Python tool and builds the tpr container images,
but it never installs `tpr-native` on the host. `verify` checks the tpr CLI,
version, contract and image presence, so a fresh machine is green while the
first `RUNTIME__PALETTE__PRODUCER=tpr` wallpaper set fails.

This is a direct cutover blocker and a likely contributor to the rofi failure
in BUG-006: if runtime-seed runs with the tpr producer before the helper exists,
it fails and accepts rc 1.

## Evidence

Runtime adapter behavior:

```text
dotfiles-runtime/src/runtime/adapters/tpr_adapter.py
  env = build_env({
      ...
      "THEME__GENERATION__ENGINE": self._engine,
      "THEME__RUNTIME__MODE": "local",
  })
```

Native engine availability is a PATH probe:

```text
theme-producer/src/theme_producer/adapters/engines/native.py
  def is_available(self) -> bool:
      return shutil.which(BINARY_NAME) is not None
```

Fresh-host observation after bootstrap:

```text
$ tpr list-engines | jq '.engines[] | select(.name=="native")'
{ "name": "native", "available": false, "image_available": true,
  "image": "tpr-native-podman:v0.4.0" }

$ RUNTIME__PALETTE__PRODUCER=tpr RUNTIME__PALETTE__TPR_ENGINE=native \
    dotfiles-runtime wallpaper set /home/inumaki/.local/share/dotfiles/wallpapers/default.png
ERROR ... EngineUnavailableError: engine 'native' is not available on this host;
run `tpr install --engine native` and use `--runtime container`, or install the engine binary
```

The failure is recorded in `~/.local/state/dotfiles/failures.jsonl` at
`2026-10-29T22:31:45Z`, stage `palette`, tool reported as `csg` by the older
runtime error path but the stderr is the tpr `EngineUnavailableError`.

Manual proof and workaround:

```text
$ install -m 0755 theme-producer/native/target/release/tpr-native \
    /home/inumaki/.local/bin/tpr-native
$ tpr-native --version
0.1.0
$ tpr list-engines | jq ...
{ "name": "native", "available": true, ... }
```

After this, the tpr/native set succeeded (`palette 01c9360b…`), and direct tpr
generation matched the runtime cache artifacts byte-for-byte.

`tpr install --engine native` builds the image `tpr-native-<engine>:v0.4.0`; it
does not install a host binary. The engine role builds/verifies that image, but
does not extract or install the helper.

## Fix options

1. **Provision the helper from the already-built image (preferred for the
   current local adapter).** In `cli_tools`/`runtime_daemon`, after the tpr
   native image exists, extract the helper (for example, copy the binary out of
   `tpr-native-<engine>:<tag>` into `$XDG_BIN_HOME`) and make it executable;
   add a `verify` check for `tpr-native --version` and native availability when
   `runtime_palette_producer=tpr`. No Rust toolchain is required if the image is
   the source of truth.
2. **Use the container path.** Make `TprAdapter` honour the tpr settings
   `[runtime].mode=container` (or use the native image) instead of forcing
   `local`; then no host helper is needed. This requires a runtime release and
   an engine pin, but matches the “containerized engine” requirement.
3. **Fail loud / correct the seed.** At minimum, runtime-seed and verify must
   reject a selected tpr producer when `tpr-native` is unavailable, instead of
   accepting rc 1 and leaving a broken first wallpaper set.

Do not make the manual `~/.local/bin` copy the only supported path.

## Triage decision (2026-10-29)

The proper fix is **container mode**, not a host `tpr-native` extraction.
`tpr-native-podman:v0.4.0` already contains both `tpr` and `tpr-native`; the
adapter was overriding the provisioned `[runtime].mode = "container"` with
`local`. A container-mode prototype produced the same eight artifacts as the
verified local tpr entry. This keeps the “host never installs backend binaries”
contract and removes the manual `~/.local/bin` copy.

Implementation split:

- `dotfiles-runtime` REQ-005 — stop forcing local, pin the spine templates dir,
  use container native; release runtime.
- `dotfiles-runtime` REQ-004 — producer config (also fixes the seed env
  mismatch); release runtime.
- `dotfiles-provision` — render `config/dotfiles-runtime/producer.json`, remove
  env.d/unit producer authority, remove the native-helper requirement, add a
  real bounded tpr generate in verify when the selected producer is tpr, and
  bump the runtime pin.
- runtime-seed no longer needs producer env; see BUG-008.
- BUG-006 remains separate: the rofi pre/post-seed exposure and missing verify
  consumer link are independent of the native engine.

## Done-when

- [ ] On a fresh host, bootstrap with `runtime_palette_producer=tpr` and
  `scheme_type=scheme-tonal-spot` produces a working first
  `dotfiles-runtime wallpaper set` with the native engine, with no manual
  install.
- [ ] `verify` asserts the selected producer can actually generate (native
  helper present, or container mode configured), not just that images exist.
- [ ] `runtime-seed` does not succeed with rc 1 when the selected producer is
  unusable.
- [ ] The chosen fix is recorded with the engine version/tag and any runtime
  pin bump.

## Cross-references

- `dotfiles-provision` BUG-006 — rofi failed after bootstrap until a wallpaper
  set; a failed tpr runtime-seed is a candidate cause.
- `dotfiles-runtime` REQ-003 — producer seam; `TprAdapter` local mode.
- `theme-producer` native engine packaging/`tpr install` behavior.
