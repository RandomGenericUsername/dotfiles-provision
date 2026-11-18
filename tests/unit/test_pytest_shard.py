"""REQ-055: deterministic pytest sharding and the slow-marker contract."""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import pytest_shard  # noqa: E402


def _all_test_files() -> list[str]:
    return pytest_shard.discover_test_files(ROOT)


# --- coverage and overlap ---------------------------------------------------


@pytest.mark.parametrize("total", [1, 2, 3, 4, 7, 10])
def test_every_file_is_assigned_to_exactly_one_shard(total: int) -> None:
    files = _all_test_files()
    shards = [pytest_shard.select_files(files, index, total) for index in range(1, total + 1)]
    flattened = [path for shard in shards for path in shard]

    assert sorted(flattened) == files
    assert len(flattened) == len(files)
    assert any(shards), "a shard must not be empty for the real test tree"
    for shard in shards:
        assert len(shard) == len(set(shard))


def test_selection_is_deterministic_and_order_stable() -> None:
    files = _all_test_files()
    first = pytest_shard.select_files(files, 2, 4)
    second = pytest_shard.select_files(list(files), 2, 4)
    assert first == second
    assert first == sorted(first)


def test_four_shards_cover_the_fast_suite_without_duplicates() -> None:
    fast = pytest_shard.fast_files(_all_test_files())
    shards = [pytest_shard.select_files(fast, index, 4) for index in range(1, 5)]

    assert all(shards), "every CI shard must select at least one fast test file"
    flattened = [path for shard in shards for path in shard]
    assert sorted(flattened) == fast
    assert not any(path.startswith("tests/integration/") for path in fast)


# --- validation / list mode -------------------------------------------------


@pytest.mark.parametrize(
    "value",
    ["", "1", "1/0", "0/4", "5/4", "a/b", "1/2/3"],
)
def test_invalid_shard_values_fail_closed(value: str) -> None:
    with pytest.raises(pytest_shard.ShardError):
        pytest_shard.parse_shard(value)


def test_valid_shard_is_one_based() -> None:
    assert pytest_shard.parse_shard("1/4") == (1, 4)
    assert pytest_shard.parse_shard("4/4") == (4, 4)


def test_script_lists_selected_files_without_running_pytest() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "pytest_shard.py"),
            "--shard",
            "1/4",
            "--fast",
            "--list",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    listed = [line for line in proc.stdout.splitlines() if line.strip()]
    assert listed
    assert listed == sorted(listed)
    assert all(line.startswith("tests/") and line.endswith(".py") for line in listed)
    assert "passed" not in proc.stdout and "collected" not in proc.stdout


def test_script_rejects_an_empty_shard(monkeypatch, capsys) -> None:
    monkeypatch.setattr(pytest_shard, "discover_test_files", lambda root: ["tests/a.py"])
    # 1/2 selects the single file; 2/2 would be empty and must fail, not
    # silently run the full suite.
    assert pytest_shard.main(["--shard", "2/2", "--root", str(ROOT)]) == 1
    assert "selected no files" in capsys.readouterr().err


# --- slow marker / make contract -------------------------------------------


def _pyproject() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_slow_marker_is_registered() -> None:
    markers = _pyproject()["tool"]["pytest"]["ini_options"]["markers"]
    assert any(marker.startswith("slow:") for marker in markers), markers


def test_make_test_remains_the_full_fast_suite_and_test_fast_excludes_slow() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert 'FAST := -m "not integration and not container_target"' in makefile
    assert 'TEST_FAST := -m "not integration and not container_target and not slow"' in makefile
    assert "\ntest-fast:" in makefile
    assert "\ntest-shard:" in makefile

    fast_recipe = makefile.split("\ntest-fast:", 1)[1].split("\n\n", 1)[0]
    assert "$(TEST_FAST)" in fast_recipe
    test_recipe = makefile.split("\ntest:", 1)[1].split("\n\n", 1)[0]
    assert "$(FAST)" in test_recipe


def test_slow_marks_are_a_nonempty_strict_subset() -> None:
    marked = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "tests").rglob("test_*.py")
        if re.search(
            r"^pytestmark\s*=\s*pytest\.mark\.slow\b",
            path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
    )
    all_files = sorted(_all_test_files())
    assert marked, "at least one demonstrably slow module must carry the marker"
    assert set(marked) < set(all_files), "do not mark the whole suite slow"
    # Keep the marker an exception, not the default.
    assert len(marked) < len(all_files) / 2
