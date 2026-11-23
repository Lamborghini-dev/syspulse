import json
from pathlib import Path
from typing import Annotated

from rich.console import Console
from rich.table import Table
import typer

from syspulse.metrics import collect_snapshot

app = typer.Typer(help="System telemetry and diagnostic CLI.")
console = Console()


@app.command()
def snapshot(
    disk: Annotated[str, typer.Option("--disk", "-d", help="Drive path to inspect.")] = "C:\\",
    json_out: Annotated[Path | None, typer.Option("--json-out", help="Optional path to save JSON output.")] = None,
) -> None:
    """Collect and display a live CPU, RAM, and disk snapshot."""
    data = collect_snapshot(disk_path=disk)

    table = Table(title="System Snapshot")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", justify="right")

    table.add_row("CPU Usage", f"{data.cpu_percent:.1f}%")
    table.add_row("RAM Usage", f"{data.ram_used_gb:.2f} / {data.ram_total_gb:.2f} GB ({data.ram_percent:.1f}%)")
    table.add_row(f"Disk ({disk}) Free", f"{data.disk_free_gb:.2f} GB ({100 - data.disk_percent:.1f}% free)")

    console.print(table)

    if json_out is not None:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(data.__dict__, indent=2), encoding="utf-8")
        console.print(f"[green]Saved JSON report to {json_out}[/green]")