import json
from pathlib import Path
from typing import Annotated

from rich.console import Console
from rich.table import Table
import typer

from syspulse.metrics import collect_snapshot
from syspulse.network import check_tcp_latency

app = typer.Typer(help="System telemetry and diagnostic CLI.")
console = Console()


@app.command()
def main(
    disk: Annotated[str, typer.Option("--disk", "-d", help="Drive path to inspect.")] = "C:\\",
    ping_host: Annotated[str, typer.Option("--ping-host", help="Target host for TCP latency check.")] = "1.1.1.1",
    ping_port: Annotated[int, typer.Option("--ping-port", help="Target TCP port for latency check.")] = 443,
    json_out: Annotated[Path | None, typer.Option("--json-out", help="Optional path to save JSON output.")] = None,
) -> None:
    """Collect and display a live CPU, RAM, disk, and TCP latency snapshot."""
    snap = collect_snapshot(disk_path=disk)
    net = check_tcp_latency(host=ping_host, port=ping_port)

    table = Table(title="System Snapshot")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", justify="right")

    table.add_row("CPU Usage", f"{snap.cpu_percent:.1f}%")
    table.add_row("RAM Usage", f"{snap.ram_used_gb:.2f} / {snap.ram_total_gb:.2f} GB ({snap.ram_percent:.1f}%)")
    table.add_row(f"Disk ({disk}) Free", f"{snap.disk_free_gb:.2f} GB ({100 - snap.disk_percent:.1f}% free)")

    if net.reachable and net.latency_ms is not None:
        latency_str = f"{net.latency_ms:.2f} ms ({net.host}:{net.port})"
    else:
        latency_str = f"Unreachable ({net.host}:{net.port})"
    table.add_row("TCP Latency", latency_str)

    console.print(table)

    if json_out is not None:
        payload = {
            "snapshot": snap.__dict__,
            "network": net.__dict__,
        }
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        console.print(f"[green]Saved JSON report to {json_out}[/green]")