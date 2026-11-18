#!/usr/bin/env python3
"""Deterministic pytest file sharding (REQ-055).

Selection is intentionally simple and stable: discover every ``tests/**/test_*.py``
file, sort the repository-relative paths, then assign index ``i`` to shard
``i % N + 1``. Running all ``I/N`` selections therefore covers every file exactly
once, with no overlap and no omission. Adding a test file can move other files
between shards, but a given tree always produces the same assignment.

This script only *selects* files; it never runs pytest. ``make test-shard``
passes the selected paths to pytest together with the fast marker expression.

Usage::

    python3 scripts/pytest_shard.py --shard 1/4
    python3 scripts/pytest_shard.py --shard 2/4 --fast
    python3 scripts/pytest_shard.py --shard 1/4 --list
    make test-shard SHARD=1/4
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ShardError(RuntimeError):
    """Invalid shard selection or an empty test tree."""


def discover_test_files(root: Path) -> list[str]:
    """Return every pytest test module, repository-relative, sorted."""
    tests = root / "tests"
    if not tests.is_dir():
        raise ShardError(f"test directory not found: {tests}")
    files = sorted(
        path.relative_to(root).as_posix() for path in tests.rglob("test_*.py") if path.is_file()
    )
    if not files:
        raise ShardError(f"no test_*.py files found under {tests}")
    return files


def parse_shard(value: str) -> tuple[int, int]:
    """Parse ``I/N`` (1-based) and fail closed on anything else."""
    parts = value.split("/")
    if len(parts) != 2:
        raise ShardError(f"shard must be I/N, got `{value}`")
    try:
        index, total = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ShardError(f"shard must be I/N with integers, got `{value}`") from exc
    if total < 1:
        raise ShardError(f"shard count must be >= 1, got {total}")
    if index < 1 or index > total:
        raise ShardError(f"shard index must be 1..{total}, got {index}")
    return index, total


def select_files(files: list[str], index: int, total: int) -> list[str]:
    """Assign sorted files round-robin; every file lands in exactly one shard."""
    if not 1 <= index <= total:
        raise ShardError(f"shard index must be 1..{total}, got {index}")
    return [path for position, path in enumerate(files) if position % total == index - 1]


def fast_files(files: list[str]) -> list[str]:
    """Drop the real-ansible integration tree from a fast-suite shard."""
    return [path for path in files if not path.startswith("tests/integration/")]


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard", required=True, help="shard selection I/N (1-based)")
    parser.add_argument("--root", default=str(ROOT), help="repository root")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="exclude tests/integration/ (the fast suite selection)",
    )
    parser.add_argument(
        "--list",
        "--dry-run",
        dest="list_only",
        action="store_true",
        help="print the selected files (the default action; accepted for clarity)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root = Path(args.root).resolve()
    try:
        index, total = parse_shard(args.shard)
        files = discover_test_files(root)
        if args.fast:
            files = fast_files(files)
        selected = select_files(files, index, total)
    except ShardError as exc:
        print(f"pytest-shard: {exc}", file=sys.stderr)
        return 2

    if not selected:
        print(f"pytest-shard: shard {index}/{total} selected no files", file=sys.stderr)
        return 1
    for path in selected:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
