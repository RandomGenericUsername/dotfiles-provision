# Design — power-options Bluetooth policy

## D1. Rewrite the package-owned TOML, do not copy it

The profile files carry much more than `block_bt` (CPU, RAPL, network, ASPM, …). Static copies
would freeze those settings and drift on package updates. `ansible.builtin.replace` flips only the
one line, is idempotent, and preserves every other package default.

## D2. Arch-only by layout, not by fact

`/etc/power-options/profiles` exists only where the power-options package is installed. The role
stats it once and skips every mutation when absent; on Arch it asserts the three expected files
exist (a package rename fails loud rather than silently leaving Bluetooth blocked). No
`ansible_os_family` branch is needed.

## D3. Refresh only when a profile changed

`power-options-daemon` applies the active profile from the files. `power-daemon-mgr refresh-full`
makes the change effective immediately, but running it unconditionally reports `changed` on every
bootstrap. It is gated on the replace loop's `changed` flag and runs with `changed_when: false`.

## D4. Verify the deployed files

`verify` reads the three files with `slurp` and asserts `block_bt = false` in each. The directory
check keeps non-Arch hosts green. This catches a package update that reinstalls `true` even if the
role never ran on that host.

## D5. Bootstrap placement

`power-options.yaml` is imported right after `packages.yaml`: the package owns the files, and a
failure there aborts before the expensive CLI/image work. It has no dependency on the assets spine.

## Verification plan

| Claim | Command | Expected |
| --- | --- | --- |
| Source layout | `uv run pytest -q tests/unit/test_power_options_role.py tests/unit/test_bootstrap_playbook.py` | exit 0 |
| No blocking flag | `grep -H block_bt /etc/power-options/profiles/*.toml` after apply | all `false` |
| Verify gate | `dotfiles-provision verify` | exit 0 on Arch |
| Idempotent | second `power-options.yaml` run | `changed=0` |
