from dataclasses import dataclass
import socket
import time


@dataclass
class LatencyCheckResult:
    host: str
    port: int
    reachable: bool
    latency_ms: float | None
    error: str | None = None


def check_tcp_latency(host: str = "1.1.1.1", port: int = 443, timeout: float = 2.0) -> LatencyCheckResult:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return LatencyCheckResult(
                host=host,
                port=port,
                reachable=True,
                latency_ms=elapsed_ms,
                error=None,
            )
    except OSError as exc:
        return LatencyCheckResult(
            host=host,
            port=port,
            reachable=False,
            latency_ms=None,
            error=str(exc),
        )