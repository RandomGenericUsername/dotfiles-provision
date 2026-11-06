"""REQ-023: always-on AGS systemd --user supervision.

Two independent layers are pinned here:

1. the unit template renders the bar and notifications contracts from the one
   app-list identity (instance + spine config path), and
2. the shared ``ags-run-locked`` wrapper's new ``--exec`` mode refuses a
   delegated start and closes its flock descriptor before the exec.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader

_ENGINE_ROOT = Path(__file__).resolve().parents[2]
_ROLES_DIR = _ENGINE_ROOT / "ansible" / "roles"
_TEMPLATES = _ROLES_DIR / "ags_apps_units" / "templates"
_WRAPPER = _ROLES_DIR / "cli_tools" / "files" / "ags-run-locked"


def _always_on_apps() -> list[dict[str, Any]]:
    fixture = _ENGINE_ROOT / "tests" / "fixtures" / "ags-apps" / "app-list" / "all-standalone.apps.yaml"
    document = yaml.safe_load(fixture.read_text(encoding="utf-8"))
    return [entry for entry in document["apps"] if entry["launch"] == "always"]


def _render_unit(app: dict[str, Any], *, install: str = "/home/u/.local/share/dotfiles") -> str:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES)),
        autoescape=False,
        keep_trailing_newline=True,
    )
    template = env.get_template("dotfiles-ags-app.service.j2")
    return template.render(
        app=app,
        ags_apps_units_run_locked="/home/u/.local/bin/ags-run-locked",
        ags_apps_units_ags_bin="/usr/bin/ags",
        ags_apps_units_spine_link=f"{install}/config/{app['spineLink']}",
        ags_apps_units_lock_timeout=10,
        ags_apps_units_register_timeout=10,
        ags_apps_units_restart_sec=2,
        ags_apps_units_timeout_stop_sec=10,
        ags_apps_units_start_limit_interval_sec=60,
        ags_apps_units_start_limit_burst=3,
    )


class TestUnitTemplateRendering:
    def test_only_bar_and_notifications_are_always_on(self) -> None:
        assert [entry["app"] for entry in _always_on_apps()] == ["bar", "notifications"]

    def test_bar_unit_matches_the_manifest_identity(self) -> None:
        app = next(entry for entry in _always_on_apps() if entry["app"] == "bar")
        text = _render_unit(app)
        assert "ExecStart=/home/u/.local/bin/ags-run-locked --exec" in text
        assert "--expect-instance ags" in text
        assert "-- /usr/bin/ags run -d /home/u/.local/share/dotfiles/config/ags" in text
        assert "ExecStop=/usr/bin/ags quit -i ags" in text

    def test_notifications_unit_matches_the_manifest_identity(self) -> None:
        app = next(entry for entry in _always_on_apps() if entry["app"] == "notifications")
        text = _render_unit(app)
        assert "--expect-instance notifications" in text
        assert (
            "-- /usr/bin/ags run -d "
            "/home/u/.local/share/dotfiles/config/ags-notifications"
        ) in text
        assert "ExecStop=/usr/bin/ags quit -i notifications" in text

    def test_every_always_on_unit_carries_the_frozen_policy(self) -> None:
        for app in _always_on_apps():
            text = _render_unit(app)
            assert "PartOf=graphical-session.target" in text
            assert "After=graphical-session.target" in text
            assert "Type=simple" in text
            assert "Restart=on-failure" in text
            assert "RestartSec=2" in text
            assert "TimeoutStopSec=10" in text
            assert "KillMode=mixed" in text
            assert "WantedBy=default.target" in text
            # The unit never backgrounds or raw-starts outside the wrapper.
            assert text.count("ExecStart=") == 1
            assert "ExecStart=/usr/bin/ags" not in text

    def test_on_demand_apps_have_no_unit_in_the_app_list(self) -> None:
        fixture = _ENGINE_ROOT / "tests" / "fixtures" / "ags-apps" / "app-list" / "all-standalone.apps.yaml"
        document = yaml.safe_load(fixture.read_text(encoding="utf-8"))
        on_demand = {entry["app"] for entry in document["apps"] if entry["launch"] == "on-demand"}
        assert on_demand == {
            "capture",
            "clipboard",
            "wallpaper-selector",
            "icme",
            "btop-theme-studio",
        }
        assert {entry["app"] for entry in _always_on_apps()} == {"bar", "notifications"}


def _wrapper_env(tmp_path: Path, registry: str = "") -> tuple[dict[str, str], Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "ags-calls"
    fake_ags = bin_dir / "ags"
    fake_ags.write_text(
        "#!/usr/bin/env bash\n"
        'REG="${FAKE_AGS_REGISTRY:?}"\n'
        'CALLS="${FAKE_AGS_CALLS:?}"\n'
        'case "$1" in\n'
        '  list) cat "$REG" 2>/dev/null || true ;;\n'
        '  run) printf "run %s\\n" "$*" >> "$CALLS" ;;\n'
        "esac\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ags.chmod(0o755)
    registry_path = tmp_path / "registry"
    registry_path.write_text(registry + ("\n" if registry else ""), encoding="utf-8")
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    env = dict(
        os.environ,
        PATH=f"{bin_dir}:{os.environ.get('PATH', '')}",
        XDG_RUNTIME_DIR=str(runtime),
        FAKE_AGS_REGISTRY=str(registry_path),
        FAKE_AGS_CALLS=str(calls),
    )
    return env, calls


class TestExecWrapper:
    def test_delegated_start_is_a_failure(self, tmp_path: Path) -> None:
        env, calls = _wrapper_env(tmp_path, registry="unit-test")
        result = subprocess.run(
            [
                str(_WRAPPER),
                "--exec",
                "--expect-instance",
                "unit-test",
                "--lock-timeout",
                "1",
                "--register-timeout",
                "1",
                "--",
                "/bin/true",
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        assert result.returncode != 0, "a delegated --exec start must fail the unit"
        assert "already running" in result.stderr
        assert "delegated" in result.stderr
        assert not calls.exists() or calls.read_text() == ""

    def test_exec_closes_the_flock_fd(self, tmp_path: Path) -> None:
        env, calls = _wrapper_env(tmp_path)
        result = subprocess.run(
            [
                str(_WRAPPER),
                "--exec",
                "--expect-instance",
                "unit-test",
                "--lock-timeout",
                "1",
                "--register-timeout",
                "1",
                "--",
                "/bin/bash",
                "-c",
                'if : >&9 2>/dev/null; then echo OPEN; else echo CLOSED; fi',
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "CLOSED", (
            "the app must not inherit the launch-lock fd (9>&- before exec)"
        )
        assert not calls.exists() or calls.read_text() == ""

    def test_exec_runs_the_supplied_command_in_the_foreground(self, tmp_path: Path) -> None:
        env, _ = _wrapper_env(tmp_path)
        marker = tmp_path / "marker"
        result = subprocess.run(
            [
                str(_WRAPPER),
                "--exec",
                "--expect-instance",
                "unit-test",
                "--",
                "/bin/bash",
                "-c",
                f'printf "%s" "$0" > "{marker}"',
                "foreground",
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert marker.read_text() == "foreground"

    def test_timeout_cleanup_never_kills_the_ags_run_parent(self) -> None:
        text = _WRAPPER.read_text(encoding="utf-8")
        assert 'kill "$child"' not in text
        assert 'ags quit -i "$expect_instance"' in text

    def test_background_mode_still_delegates_cleanly(self, tmp_path: Path) -> None:
        env, _ = _wrapper_env(tmp_path, registry="unit-test")
        result = subprocess.run(
            [
                str(_WRAPPER),
                "--expect-instance",
                "unit-test",
                "--lock-timeout",
                "1",
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
