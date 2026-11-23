from syspulse.metrics import SystemSnapshot, collect_snapshot


def test_collect_snapshot_returns_valid_ranges() -> None:
    snap = collect_snapshot("C:\\")
    assert isinstance(snap, SystemSnapshot)
    assert 0.0 <= snap.cpu_percent <= 100.0
    assert 0.0 <= snap.ram_percent <= 100.0
    assert snap.ram_total_gb > 0
    assert snap.disk_free_gb >= 0