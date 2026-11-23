from unittest.mock import patch

from syspulse.network import LatencyCheckResult, check_tcp_latency


def test_check_tcp_latency_unreachable() -> None:
    with patch("syspulse.network.socket.create_connection", side_effect=OSError("timed out")):
        result = check_tcp_latency(host="192.0.2.1", port=443, timeout=0.1)

    assert isinstance(result, LatencyCheckResult)
    assert result.reachable is False
    assert result.latency_ms is None
    assert result.error == "timed out"