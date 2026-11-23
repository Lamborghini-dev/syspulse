from types import SimpleNamespace
from unittest.mock import patch

from syspulse.diagnostics import collect_gaming_audit, get_active_power_scheme


def test_get_active_power_scheme_parses_parentheses():
    mock_result = SimpleNamespace(
        stdout="Power Scheme GUID: 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c  (High performance)\n",
        stderr="",
    )
    with patch("syspulse.diagnostics.subprocess.run", return_value=mock_result):
        assert get_active_power_scheme() == "High performance"


def test_collect_gaming_audit_flags_low_disk_and_sorts_processes():
    fake_disk = SimpleNamespace(free=10 * (1024**3))
    fake_procs = [
        SimpleNamespace(
            info={"pid": 101, "name": "small.exe", "memory_info": SimpleNamespace(rss=128 * (1024**2))},
            cpu_percent=lambda interval=None: 1.5,
        ),
        SimpleNamespace(
            info={"pid": 202, "name": "heavy.exe", "memory_info": SimpleNamespace(rss=1024 * (1024**2))},
            cpu_percent=lambda interval=None: 12.0,
        ),
    ]

    with (
        patch("syspulse.diagnostics.get_active_power_scheme", return_value="Balanced"),
        patch("syspulse.diagnostics.psutil.disk_usage", return_value=fake_disk),
        patch("syspulse.diagnostics.psutil.process_iter", return_value=fake_procs),
    ):
        report = collect_gaming_audit(disk_path="C:\\", min_free_gb=25.0, top_n=2)

    assert report.power_scheme == "Balanced"
    assert report.disk_free_gb == 10.0
    assert report.disk_low_space_warning is True
    assert [p.name for p in report.top_memory_processes] == ["heavy.exe", "small.exe"]
