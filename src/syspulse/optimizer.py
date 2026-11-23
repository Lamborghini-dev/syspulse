from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess

from syspulse.diagnostics import get_active_power_scheme

HIGH_PERFORMANCE_GUID = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
BALANCED_GUID = "381b4222-f694-41f0-9685-ff5bb260df2e"
POWER_SAVER_GUID = "a1841308-3541-4fab-bc81-f71556f20b4a"

PROTECTED_PROCESSES: frozenset[str] = frozenset(
    {
        "system",
        "registry",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "fontdrvhost.exe",
        "dwm.exe",
        "explorer.exe",
        "memcompression",
        "tiworker.exe",
        "trustedinstaller.exe",
        "wudfhost.exe",
        "audiodg.exe",
    }
)


@dataclass(frozen=True)
class OptimizationAction:
    name: str
    category: str
    risk: str
    reversible: bool
    detail: str
    estimated_reclaim_mb: float = 0.0
    applied: bool = False


@dataclass(frozen=True)
class OptimizationResult:
    dry_run: bool
    previous_power_scheme: str
    target_power_scheme: str
    temp_dir: str
    temp_size_mb: float
    actions: list[OptimizationAction]
    rollback_path: str | None = None


def estimate_temp_usage_mb(temp_dir: Path | None = None) -> tuple[Path, float, int]:
    target = temp_dir or Path(os.environ.get("TEMP", "C:\\Windows\\Temp"))
    total_bytes = 0
    file_count = 0

    if not target.exists():
        return target, 0.0, 0

    for root, _, files in os.walk(target):
        for fname in files:
            fpath = Path(root) / fname
            try:
                total_bytes += fpath.stat().st_size
                file_count += 1
            except OSError:
                continue

    return target, round(total_bytes / (1024**2), 2), file_count


def clean_temp_files(temp_dir: Path, dry_run: bool = True) -> float:
    if not temp_dir.exists():
        return 0.0

    reclaimed_bytes = 0
    for item in temp_dir.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                size = item.stat().st_size
                if not dry_run:
                    item.unlink(missing_ok=True)
                reclaimed_bytes += size
            elif item.is_dir():
                dir_bytes = sum(
                    f.stat().st_size
                    for f in item.rglob("*")
                    if f.is_file()
                )
                if not dry_run:
                    shutil.rmtree(item, ignore_errors=True)
                reclaimed_bytes += dir_bytes
        except OSError:
            continue

    return round(reclaimed_bytes / (1024**2), 2)


def set_power_scheme(scheme_guid: str) -> bool:
    try:
        completed = subprocess.run(
            ["powercfg", "/setactive", scheme_guid],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return completed.returncode == 0
    except Exception:
        return False


def save_rollback_snapshot(
    rollback_file: Path,
    previous_power_scheme: str,
    target_power_guid: str,
) -> Path:
    rollback_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "previous_power_scheme": previous_power_scheme,
        "target_power_guid": target_power_guid,
    }
    rollback_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return rollback_file


def restore_from_rollback(rollback_file: Path) -> dict[str, object]:
    data = json.loads(rollback_file.read_text(encoding="utf-8"))
    previous_scheme = str(data.get("previous_power_scheme", "Balanced")).strip()
    guid_map = {
        "high performance": HIGH_PERFORMANCE_GUID,
        "balanced": BALANCED_GUID,
        "power saver": POWER_SAVER_GUID,
    }
    target_guid = guid_map.get(previous_scheme.lower(), BALANCED_GUID)
    restored = set_power_scheme(target_guid)
    return {
        "restored": restored,
        "previous_power_scheme": previous_scheme,
        "applied_guid": target_guid,
    }


def run_optimization(
    dry_run: bool = True,
    clean_temp: bool = True,
    target_power_guid: str = HIGH_PERFORMANCE_GUID,
    temp_dir: Path | None = None,
    rollback_path: Path | None = None,
) -> OptimizationResult:
    current_scheme = get_active_power_scheme()
    resolved_temp, temp_mb, file_count = estimate_temp_usage_mb(temp_dir=temp_dir)
    actions: list[OptimizationAction] = []

    power_already_high = current_scheme.lower() == "high performance"
    power_applied = False
    saved_rollback: str | None = None

    if not power_already_high:
        if not dry_run:
            if rollback_path is not None:
                save_rollback_snapshot(
                    rollback_file=rollback_path,
                    previous_power_scheme=current_scheme,
                    target_power_guid=target_power_guid,
                )
                saved_rollback = str(rollback_path)
            power_applied = set_power_scheme(target_power_guid)
        actions.append(
            OptimizationAction(
                name="Switch Power Plan to High Performance",
                category="power",
                risk="low",
                reversible=True,
                detail=f"Change active power plan from '{current_scheme}' to High performance ({target_power_guid}).",
                applied=power_applied,
            )
        )
    else:
        actions.append(
            OptimizationAction(
                name="Power Plan Already High Performance",
                category="power",
                risk="none",
                reversible=True,
                detail="Active power scheme is already set to High performance.",
                applied=False,
            )
        )

    if clean_temp:
        reclaimed = clean_temp_files(resolved_temp, dry_run=dry_run)
        actions.append(
            OptimizationAction(
                name="Clean Temporary Files",
                category="storage",
                risk="low",
                reversible=False,
                detail=f"Scan/clean {file_count} temp file(s) in '{resolved_temp}'.",
                estimated_reclaim_mb=reclaimed if not dry_run else temp_mb,
                applied=not dry_run,
            )
        )

    return OptimizationResult(
        dry_run=dry_run,
        previous_power_scheme=current_scheme,
        target_power_scheme="High performance",
        temp_dir=str(resolved_temp),
        temp_size_mb=temp_mb,
        actions=actions,
        rollback_path=saved_rollback,
    )


def result_to_dict(result: OptimizationResult) -> dict[str, object]:
    return {
        "dry_run": result.dry_run,
        "previous_power_scheme": result.previous_power_scheme,
        "target_power_scheme": result.target_power_scheme,
        "temp_dir": result.temp_dir,
        "temp_size_mb": result.temp_size_mb,
        "rollback_path": result.rollback_path,
        "actions": [asdict(action) for action in result.actions],
    }
