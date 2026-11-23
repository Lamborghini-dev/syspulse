import json
from pathlib import Path
from typing import Annotated

from rich.console import Console
from rich.table import Table
import typer

from syspulse.diagnostics import collect_gaming_audit
from syspulse.metrics import collect_snapshot
from syspulse.network import check_tcp_latency

app = typer.Typer(help="System telemetry and diagnostic CLI.")
console = Console()


def _run_snapshot(
    disk: str = "C:\\",
    ping_host: str = "1.1.1.1",
    ping_port: int = 443,
    json_out: Path | None = None,
) -> None:
    snap = collect_snapshot(disk_path=disk)
    net = check_tcp_latency(host=ping_host, port=ping_port)

    table = Table(title="System Snapshot")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", justify="right")

    table.add_row("CPU Usage", f"{snap.cpu_percent:.1f}%")
    table.add_row(
        "RAM Usage",
        f"{snap.ram_used_gb:.2f} / {snap.ram_total_gb:.2f} GB ({snap.ram_percent:.1f}%)",
    )
    table.add_row(
        f"Disk ({disk}) Free",
        f"{snap.disk_free_gb:.2f} GB ({100 - snap.disk_percent:.1f}% free)",
    )

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


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    disk: Annotated[str, typer.Option("--disk", "-d", help="Drive path to inspect.")] = "C:\\",
    ping_host: Annotated[str, typer.Option("--ping-host", help="Target host for TCP latency check.")] = "1.1.1.1",
    ping_port: Annotated[int, typer.Option("--ping-port", help="Target TCP port for latency check.")] = 443,
    json_out: Annotated[Path | None, typer.Option("--json-out", help="Optional path to save JSON output.")] = None,
) -> None:
    """Collect and display a live CPU, RAM, disk, and TCP latency snapshot."""
    if ctx.invoked_subcommand is None:
        _run_snapshot(disk=disk, ping_host=ping_host, ping_port=ping_port, json_out=json_out)


@app.command()
def audit(
    disk: Annotated[str, typer.Option("--disk", "-d", help="Drive path to inspect for gaming headroom.")] = "C:\\",
    min_free_gb: Annotated[float, typer.Option("--min-free-gb", help="Minimum free GB threshold before warning.")] = 25.0,
    top_n: Annotated[int, typer.Option("--top-n", help="Number of top memory processes to display.")] = 5,
    json_out: Annotated[Path | None, typer.Option("--json-out", help="Optional path to save audit JSON report.")] = None,
) -> None:
    """Run read-only Windows gaming readiness and resource diagnostics."""
    report = collect_gaming_audit(disk_path=disk, min_free_gb=min_free_gb, top_n=top_n)

    summary_table = Table(title="Gaming Readiness Audit")
    summary_table.add_column("Check", style="bold cyan")
    summary_table.add_column("Status / Value", justify="right")

    summary_table.add_row("Active Power Plan", report.power_scheme)
    disk_status = f"{report.disk_free_gb:.2f} GB free"
    if report.disk_low_space_warning:
        disk_status = f"{disk_status} [yellow](LOW < {min_free_gb:.1f} GB)[/yellow]"
    summary_table.add_row(f"Disk ({report.disk_path})", disk_status)

    console.print(summary_table)

    proc_table = Table(title="Top Memory Processes")
    proc_table.add_column("PID", justify="right", style="dim")
    proc_table.add_column("Process", style="bold")
    proc_table.add_column("Memory (MB)", justify="right")
    proc_table.add_column("CPU %", justify="right")

    for proc in report.top_memory_processes:
        proc_table.add_row(
            str(proc.pid),
            proc.name,
            f"{proc.memory_mb:.1f}",
            f"{proc.cpu_percent:.1f}%",
        )

    console.print(proc_table)

    if json_out is not None:
        payload = {
            "audit": {
                "power_scheme": report.power_scheme,
                "disk_path": report.disk_path,
                "disk_free_gb": report.disk_free_gb,
                "disk_low_space_warning": report.disk_low_space_warning,
                "top_memory_processes": [p.__dict__ for p in report.top_memory_processes],
            }
        }
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        console.print(f"[green]Saved JSON report to {json_out}[/green]")
