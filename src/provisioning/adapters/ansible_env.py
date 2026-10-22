"""Child-process environment for the Ansible binaries.

A ``uv tool install`` venv contains ``ansible``/``ansible-playbook`` beside the
tool's own interpreter, but uv exposes only the project's entry points on the
tool bin dir. The CLI therefore shells to ``ansible-playbook`` and ``ansible``
through PATH and would miss the binaries that ship in its own environment.

This helper prepends the running interpreter's bin directory to the child
PATH when it is not already there. It is a no-op for an editable/``uv run``
checkout, where that directory is already first on PATH, and it makes a
self-contained wheel install (R-15) actually self-contained at runtime.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path


def with_tool_bin(env: Mapping[str, str]) -> dict[str, str]:
    """Return ``env`` with the interpreter's bin dir prepended to ``PATH``."""
    resolved = dict(env)
    bin_dir = str(Path(sys.executable).parent)
    parts = [part for part in resolved.get("PATH", "").split(os.pathsep) if part]
    if bin_dir not in parts:
        parts.insert(0, bin_dir)
    resolved["PATH"] = os.pathsep.join(parts)
    return resolved


__all__ = ["with_tool_bin"]
