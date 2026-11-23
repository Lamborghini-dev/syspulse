from types import SimpleNamespace
from unittest.mock import patch

from syspulse.diagnostics import (
    collect_gaming_audit,
    get_active_power_scheme,
    get_game_mode_status,
)


def test_get_active_power_scheme_parses_parentheses() -> None:
    fake_proc = SimpleNamespace(
        returncode=0,
        stdout="Power Scheme GUID: 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c  (High performance)\n",
    )
    with patch("syspulse.diagnostics.subprocess.run", return_value=fake_proc):
        assert get_active_power_scheme() == "High performance"


def test_get_game_mode_status_handles_missing_key() -> None:
    with patch("syspulse.diagnostics.winreg.OpenKey", side_effect=FileNotFoundError()):
        assert get_game_mode_status() is None


def test_collect_gaming_audit_flags_low_disk_and_sorts_processes() -> None:
    fake_usage = SimpleNamespace(free=10 * 1024**3)
    fake_procs = [
        SimpleNamespace(pid=101, info={"name": "small.exe"}, memory_info=lambda: SimpleNamespace(rss=120 * 1024**2), cpu_percent=lambda interval=None: 1.2),
        SimpleNamespace(pid=202, info={"name": "big.exe"}, memory_info=lambda: SimpleNamespace(rss=950 * 1024**2), cpu_percent=lambda interval=None: 8.5),
    ]

    with (
        patch("syspulse.diagnostics.get_active_power_scheme", return_value="Balanced"),
        patch("syspulse.diagnostics.get_game_mode_status", return_value=True),
        patch("syspulse.diagnostics.psutil.disk_usage", return_value=fake_usage),
        patch("syspulse.diagnostics.psutil.process_iter", return_value=fake_procs),
    ):
        report = collect_gaming_audit(disk_path="C:\\", min_free_gb=25.0, top_n=2)

    assert report.power_scheme == "Balanced"
    assert report.game_mode_enabled is True
    assert report.disk_low_space_warning is True
    assert [p.name for p in report.top_memory_processes] == ["big.exe", "small.exe"]
