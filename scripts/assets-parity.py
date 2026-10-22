#!/usr/bin/env python3
"""assets-parity — run AD-8.4 against the pinned dotfiles-assets corpus.

WHY THIS EXISTS. ``test_template_vars_parity.py`` resolves the assets corpus
through ``tests/unit/assets_templates.py``; with no checkout it SKIPS loudly.
A CI runner has no sibling checkout, so the required-var parity assertions
(forward and reverse) were never executed on a push (R-01). This runner makes
the test job provide the corpus instead of skipping:

  1. read ``assets.repo`` / ``assets.tag`` from the composition fixture (the
     same manifest the pin-mirror test reads);
  2. clone that tag into a throwaway directory — a failed clone is fatal;
  3. export ``DOTFILES_ASSETS_REPO`` and ``DOTFILES_ASSETS_TEMPLATES_DIR``;
  4. run the parity module and FAIL if any test was skipped (a skip is a
     silent pass, not evidence).

Usage: ``uv run python scripts/assets-parity.py`` (or ``make assets-parity``).
Exit 0 = every parity test executed; non-zero = test failure, clone failure,
missing templates class, or a skip.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "fixtures" / "composition" / "dotfiles" / "provisioning" / "assets.yaml"
PARITY_TEST = "tests/unit/test_template_vars_parity.py"


def _pinned_assets() -> tuple[str, str]:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assets = data["assets"]
    return str(assets["repo"]), str(assets["tag"])


def _skipped(xunit: Path) -> tuple[int, list[str]]:
    """Return (testcase count, skipped test names) from a pytest JUnit report."""
    tree = ET.parse(xunit)
    cases = list(tree.iter("testcase"))
    skipped = [
        f"{case.get('classname', '?')}::{case.get('name', '?')}"
        for case in cases
        if case.find("skipped") is not None
    ]
    return len(cases), skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the cloned corpus and print its path (debugging only)",
    )
    args = parser.parse_args()

    repo, tag = _pinned_assets()
    print(f"assets-parity: {repo} @ {tag}")

    if args.keep:
        tmp = tempfile.mkdtemp(prefix="dotfiles-assets-")
        cleanup = None
        checkout = Path(tmp) / "dotfiles-assets"
    else:
        cleanup = tempfile.TemporaryDirectory(prefix="dotfiles-assets-")
        checkout = Path(cleanup.name) / "dotfiles-assets"

    try:
        clone = subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                tag,
                "--single-branch",
                repo,
                str(checkout),
            ],
            text=True,
        )
        if clone.returncode != 0:
            print(
                "FAIL assets-parity: could not clone the pinned corpus; "
                "this job is fail-closed (no silent skip).",
                file=sys.stderr,
            )
            return 1

        templates = checkout / "templates"
        if not templates.is_dir():
            print(
                f"FAIL assets-parity: {templates} is absent in the checkout; "
                "the tag does not carry the templates class.",
                file=sys.stderr,
            )
            return 1

        if args.keep:
            print(f"checkout: {checkout}")

        env = os.environ.copy()
        env["DOTFILES_ASSETS_REPO"] = str(checkout)
        env["DOTFILES_ASSETS_TEMPLATES_DIR"] = str(templates)
        xunit = Path(cleanup.name if cleanup else checkout.parent) / "parity.xml"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                PARITY_TEST,
                "-q",
                "-rs",
                f"--junitxml={xunit}",
            ],
            cwd=ROOT,
            env=env,
        )
        if not xunit.is_file():
            print(
                "FAIL assets-parity: pytest produced no report; cannot prove the tests executed.",
                file=sys.stderr,
            )
            return 1

        total, skipped = _skipped(xunit)
        if result.returncode != 0:
            print(f"FAIL assets-parity: pytest exited {result.returncode}", file=sys.stderr)
            return result.returncode
        if skipped:
            print(
                "FAIL assets-parity: the corpus was provided but these tests "
                f"still skipped: {skipped}",
                file=sys.stderr,
            )
            return 1

        print(f"PASS assets-parity: {total} tests executed, 0 skipped")
        return 0
    finally:
        if cleanup is not None:
            cleanup.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
