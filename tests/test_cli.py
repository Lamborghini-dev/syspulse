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

def test_cli_tune_dry_run_and_json_out(tmp_path: Path) -> None:
    out_file = tmp_path / "tune.json"

    with patch("syspulse.optimizer.get_active_power_scheme", return_value="Balanced"), patch(
        "syspulse.optimizer.set_power_scheme", return_value=True
    ) as mock_set_power:
        result = runner.invoke(
            app,
            ["tune", "--no-clean-temp", "--json-out", str(out_file)],
        )

    assert result.exit_code == 0
    assert "DRY RUN" in result.stdout
    assert out_file.exists()
    mock_set_power.assert_not_called()

    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["tune"]["dry_run"] is True
    assert payload["tune"]["previous_power_scheme"] == "Balanced"


def test_cli_restore_missing_and_valid_snapshot(tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    bad_result = runner.invoke(app, ["restore", "--rollback-file", str(missing)])
    assert bad_result.exit_code == 1

    snap_file = tmp_path / "rollback.json"
    snap_file.write_text(
        json.dumps({"previous_power_scheme": "Balanced", "target_power_guid": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"}),
        encoding="utf-8",
    )

    with patch("syspulse.optimizer.set_power_scheme", return_value=True) as mock_restore:
        ok_result = runner.invoke(app, ["restore", "--rollback-file", str(snap_file)])

    assert ok_result.exit_code == 0
    assert "Restored power scheme" in ok_result.stdout
    mock_restore.assert_called_once()



