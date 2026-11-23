# syspulse

A modular Python CLI for inspecting real-time system telemetry (CPU, RAM, and disk usage) and TCP endpoint latency, with structured JSON diagnostic export.

## Project Structure

- `src/syspulse/metrics.py` - System telemetry collection via `psutil` (`SystemSnapshot`, `collect_snapshot`).
- `src/syspulse/network.py` - TCP socket latency checks (`LatencyCheckResult`, `check_tcp_latency`).
- `src/syspulse/cli.py` - Typer CLI and Rich table output with optional JSON report export.
- `tests/` - Unit and CLI integration tests powered by `pytest`.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Usage

Run a live system snapshot and TCP latency check:

```powershell
.\.venv\Scripts\syspulse.exe
```

Customize the disk path, ping target, or export a JSON report:

```powershell
.\.venv\Scripts\syspulse.exe --disk C:\ --ping-host 1.1.1.1 --ping-port 443 --json-out reports\snapshot.json
```

## Running Tests

```powershell
.\.venv\Scripts\pytest.exe -v
```
