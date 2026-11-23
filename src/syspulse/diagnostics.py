from __future__ import annotations

from dataclasses import dataclass
import subprocess
import winreg

import psutil


@dataclass(frozen=True)
class ProcessMemoryInfo:
    pid: int
    name: str
    memory_mb: float
    cpu_percent: float


@dataclass(frozen=True)
class GamingAuditReport:
    power_scheme: str
    disk_path: str
    disk_free_gb: float
    disk_low_space_warning: bool
    top_memory_processes: list[ProcessMemoryInfo]
    game_mode_enabled: bool | None = None

def get_active_power_scheme() -> str:
    try:
        completed = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return "Unknown"

    output = (completed.stdout or "").strip()
    if "(" in output and ")" in output:
        start = output.rfind("(") + 1
        end = output.rfind(")")
        if end > start:
            return output[start:end].strip()

    return output or "Unknown"


def get_game_mode_status() -> bool | None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\GameBar",
            0,
            winreg.KEY_READ,
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AutoGameModeEnabled")
            return bool(int(value))
    except FileNotFoundError:
        return None
    except OSError:
        return None
    except Exception:
        return None


def get_top_memory_processes(limit: int = 5) -> list[ProcessMemoryInfo]:
    processes: list[ProcessMemoryInfo] = []
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        try:
            mem_bytes = proc.memory_info().rss
            cpu_pct = proc.cpu_percent(interval=None)
            name = proc.info.get("name") or f"pid-{proc.pid}"
            processes.append(
                ProcessMemoryInfo(
                    pid=proc.pid,
                    name=name,
                    memory_mb=round(mem_bytes / (1024**2), 1),
                    cpu_percent=round(float(cpu_pct or 0.0), 1),
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    processes.sort(key=lambda item: item.memory_mb, reverse=True)
    return processes[: max(limit, 0)]


def collect_gaming_audit(
    disk_path: str = "C:\\",
    min_free_gb: float = 25.0,
    top_n: int = 5,
) -> GamingAuditReport:
    usage = psutil.disk_usage(disk_path)
    free_gb = round(usage.free / (1024**3), 2)
    return GamingAuditReport(
        power_scheme=get_active_power_scheme(),
        game_mode_enabled=get_game_mode_status(),
        disk_path=disk_path,
        disk_free_gb=free_gb,
        disk_low_space_warning=free_gb < min_free_gb,
        top_memory_processes=get_top_memory_processes(limit=top_n),
    )

ProcessLoad = ProcessMemoryInfo
