# syspulse

Safe, non-destructive Windows 11 gaming telemetry, diagnostics, and dry-run-first system optimization CLI built in Python.

## Features

- **Live System Snapshot (`syspulse`)**: Inspects CPU usage, RAM usage, free disk space, and TCP endpoint latency, with optional `--json-out` export.
- **Gaming Readiness Audit (`syspulse audit`)**: Checks the active Windows power scheme, flags low disk headroom (`--min-free-gb`, default `25.0`), and lists top memory-consuming processes.
-  **Dry-Run-First Optimizer (`syspulse tune`)**: Defaults to `--dry-run` so you can preview temporary file reclaim estimates and power-plan changes before applying (`@-apply`). Saves a rollback JSON snapshot (`--rollback-file`) when applying changes and protects critical system processes (`explorer.exe`, `MemCompression`, `TiWorker.exe`, and core Windows services).
-  **Rollback Restoration (`syspulse restore`)**: Restores the previous power scheme from a saved rollback snapshot.

## Setup

 ``powershell
python -m venv
 .ven\Scripts\pip.exe install -e ".[dev]"
`h``��# Usage

 ``powershell
# Default live snapshot + optional JSON export
.\venv\Scripts\syspulse.exe --disk C\\ --json-out .\reports\snapshot.json

# Read-only gaming readiness audit
..\venv\Scripts\syspulse.exe audit --disk C\\ --min-free-gb 25 --top-n 5

# Safe dry-run preview (default)
..\venv\Scripts\syspulse.exe tune

# Apply safe optimizations and save rollback state
..\venv\Scripts\syspulse.exe tune --apply --rollback-file .\.syspulse\rollback.json

# Restore from rollback snapshot
..\venv\Scripts\syspulse.exe restore --rollback-file .\.syspulse\rollback.json
```��# Running Tests

à``powershell
..\venv\Scripts\pytest.exe -v
```
