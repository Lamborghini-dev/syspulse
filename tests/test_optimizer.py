import json
from pathlib import Path
from unittest.mock import patch

from syspulse.optimizer import (
    PROTECTED_PROCESSES,
    restore_from_rollback,
    run_optimization,
)


def test_run_optimization_dry_run_does_not_delete_or_write_rollback(tmp_path: Path) -> None:
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    sample_file = temp_dir / "cache.tmp"
    sample_file.write_bytes(b"a" * (1024 * 1024))
    rollback_file = tmp_path / "rollback.json"

    with (
        patch("syspulse.optimizer.get_active_power_scheme", return_value="Balanced"),
        patch("syspulse.optimizer.set_power_scheme", return_value=True) as mock_set_power,
    ):
        result = run_optimization(
            dry_run=True,
            clean_temp=True,
            temp_dir=temp_dir,
            rollback_path=rollback_file,
        )

    assert result.dry_run is True
    assert result.rollback_path is None
    assert sample_file.exists()
    assert not rollback_file.exists()
    mock_set_power.assert_not_called()


def test_run_optimization_apply_and_restore_rollback(tmp_path: Path) -> None:
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    (temp_dir / "old.log").write_bytes(b"b" * 2048)
    rollback_file = tmp_path / "rollback.json"

    with (
        patch("syspulse.optimizer.get_active_power_scheme", return_value="Balanced"),
        patch("syspulse.optimizer.set_power_scheme", return_value=True) as mock_set_power,
    ):
        result = run_optimization(
            dry_run=False,
            clean_temp=True,
            temp_dir=temp_dir,
            rollback_path=rollback_file,
        )

    assert result.dry_run is False
    assert result.rollback_path == str(rollback_file)
    assert rollback_file.exists()
    saved = json.loads(rollback_file.read_text(encoding="utf-8"))
    assert saved["previous_power_scheme"] == "Balanced"

    with patch("syspulse.optimizer.set_power_scheme", return_value=True) as mock_restore:
        restored = restore_from_rollback(rollback_file)

    assert restored["restored"] is True
    assert restored["previous_power_scheme"] == "Balanced"
    mock_set_power.assert_called_once()
    mock_restore.assert_called_once()


def test_protected_processes_includes_critical_system_names() -> None:
    assert "explorer.exe" in PROTECTED_PROCESSES
    assert "memcompression" in PROTECTED_PROCESSES
    assert "tiworker.exe" in PROTECTED_PROCESSES
