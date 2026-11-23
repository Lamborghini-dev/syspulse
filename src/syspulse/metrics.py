from dataclasses import dataclass
import psutil


@dataclass
class SystemSnapshot:
    cpu_percent: float
    ram_percent: float
    ram_used_gb: float
    ram_total_gb: float
    disk_percent: float
    disk_free_gb: float


def collect_snapshot(disk_path: str = "C:\\") -> SystemSnapshot:
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage(disk_path)
    return SystemSnapshot(
        cpu_percent=psutil.cpu_percent(interval=0.5),
        ram_percent=vm.percent,
        ram_used_gb=round(vm.used / (1024**3), 2),
        ram_total_gb=round(vm.total / (1024**3), 2),
        disk_percent=disk.percent,
        disk_free_gb=round(disk.free / (1024**3), 2),
    )