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