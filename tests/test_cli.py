import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from syspulse.cli import app
from syspulse.metrics import SystemSnapshot
from syspulse.network import LatencyCheckResult

runner = CliRunner()


def test_cli_outputs_table_and_json(tmp_path: Path) -> None:
    snap = SystemSnapshot(
        cpu_percent=12.5,
        ram_percent=50.0,
        ram_used_gb=8.0,
        ram_total_gb=16.0,
        disk_percent=40.0,
        disk_free_gb=120.0,
    )
    net = LatencyCheckResult(
        host="1.1.1.1",
        port=443,
        reachable=True,
        latency_ms=18.42,
        error=None,
    )
    out_file = tmp_path / "snapshot.json"

    with (
        patch("syspulse.cli.collect_snapshot", return_value=snap),
        patch("syspulse.cli.check_tcp_latency", return_value=net),
    ):
        result = runner.invoke(app, ["--json-out", str(out_file)])

    assert result.exit_code == 0
    assert "System Snapshot" in result.stdout
    assert "18.42 ms" in result.stdout
    assert out_file.exists()

    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["snapshot"]["cpu_percent"] == 12.5
    assert payload["network"]["latency_ms"] == 18.42
from syspulse.diagnostics import GamingAuditReport, ProcessLoad


def test_cli_audit_command(tmp_path: Path) -> None:
    report = GamingAuditReport(
        power_scheme="Balanced",
        disk_path="C:\\",
        disk_free_gb=18.5,
        disk_low_space_warning=True,
        top_memory_processes=[
            ProcessLoad(pid=4242, name="chrome.exe", cpu_percent=4.2, memory_mb=850.5),
        ],
    )
    out_file = tmp_path / "audit.json"

    with patch("syspulse.cli.collect_gaming_audit", return_value=report):
        result = runner.invoke(app, ["audit", "--disk", "C:\\", "--json-out", str(out_file)])

    assert result.exit_code == 0
    assert "Gaming Readiness Audit" in result.stdout
    assert "Balanced" in result.stdout
    assert "chrome.exe" in result.stdout
    assert out_file.exists()

    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["audit"]["power_scheme"] == "Balanced"
    assert payload["audit"]["disk_low_space_warning"] is True
    assert payload["audit"]["top_memory_processes"][0]["name"] == "chrome.exe"
