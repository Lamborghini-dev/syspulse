from __future__ import annotations

from dataclasses import dataclass
import subprocess
import psutil


@dataclass(frozen=True)
class ProcessLoad:
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float


@dataclass(frozen=True)
class GamingAuditReport:
    power_scheme: str
    disk_path: str
    disk_free_gb: float
    disk_low_space_warning: bool
    top_memory_processes: list[ProcessLoad]


def get_active_power_scheme() -> str:
    try:
        completed = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        output = (completed.stdout or completed.stderr).strip()
        if "(" in output and ")" in output:
            return output.split("(", 1)[1].rsplit(")", 1)[0].strip()
        return output or "Unknown"
    except Exception as exc:
        return f"Unavailable ({exc})"


def collect_gaming_audit(
    disk_path: str = "C:\\",
    min_free_gb: float = 25.0,
    top_n: int = 5,
) -> GamingAuditReport:
    disk = psutil.disk_usage(disk_path)
    free_gb = round(disk.free / (1024**3), 2)

    procs: list[ProcessLoad] = []
    for proc in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            info = proc.info
            mem_info = info.get("memory_info")
            if not mem_info:
                continue
            mem_mb = round(mem_info.rss / (1024**2), 1)
            cpu_pct = round(proc.cpu_percent(interval=None), 1)
            procs.append(
                ProcessLoad(
                    pid=int(info["pid"]),
                    name=str(info.get("name") or "unknown"),
                    cpu_percent=cpu_pct,
                    memory_mb=mem_mb,
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    procs.sort(key=lambda item: item.memory_mb, reverse=True)
    return GamingAuditReport(
        power_scheme=get_active_power_scheme(),
        disk_path=disk_path,
        disk_free_gb=free_gb,
        disk_low_space_warning=free_gb < min_free_gb,
        top_memory_processes=procs[:top_n],
    )
