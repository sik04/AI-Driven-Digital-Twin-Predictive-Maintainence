"""Tests for strict raw C-MAPSS data loader with synthetic data."""

from pathlib import Path

import pytest

from intellitwin.data.loader import load_cmapss_run_to_failure
from intellitwin.data.schema import RAW_COLUMNS


def _make_valid_synthetic_data(
    num_engines: int = 3,
    cycles_per_engine: int = 5,
) -> str:
    """Generate whitespace-delimited C-MAPSS rows for testing."""
    lines: list[str] = []
    for unit in range(1, num_engines + 1):
        for cycle in range(1, cycles_per_engine + 1):
            settings = [10.0, 0.2, 100.0]
            sensors = [float(s * 10 + cycle) for s in range(1, 22)]
            row = [str(unit), str(cycle)] + [str(x) for x in settings] + [str(s) for s in sensors]
            lines.append(" ".join(row))
    return "\n".join(lines) + "\n"


def test_loader_valid_synthetic_data(tmp_path: Path) -> None:
    """Test loading valid synthetic C-MAPSS data."""
    data_str = _make_valid_synthetic_data(num_engines=3, cycles_per_engine=5)
    file_path = tmp_path / "valid.txt"
    file_path.write_text(data_str, encoding="utf-8")

    df = load_cmapss_run_to_failure(file_path, "TEST_DS", expected_engine_count=3)
    assert len(df) == 15
    assert df.shape[1] == 26
    assert list(df.columns) == list(RAW_COLUMNS)
    assert df["unit"].tolist()[:5] == [1, 1, 1, 1, 1]
    assert df["cycle"].tolist()[:5] == [1, 2, 3, 4, 5]


def test_loader_deterministic_sorting(tmp_path: Path) -> None:
    """Test that rows are sorted by unit ascending, then cycle ascending."""
    # Write rows in reverse/shuffled order
    lines: list[str] = []
    for unit in [2, 1]:
        for cycle in [3, 1, 2]:
            settings = [10.0, 0.2, 100.0]
            sensors = [1.0] * 21
            row = [str(unit), str(cycle)] + [str(x) for x in settings] + [str(s) for s in sensors]
            lines.append(" ".join(row))

    file_path = tmp_path / "shuffled.txt"
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    df = load_cmapss_run_to_failure(file_path, "TEST_DS", expected_engine_count=2)
    assert df["unit"].tolist() == [1, 1, 1, 2, 2, 2]
    assert df["cycle"].tolist() == [1, 2, 3, 1, 2, 3]


def test_loader_missing_file() -> None:
    """Test that a non-existent file raises ValueError."""
    with pytest.raises(ValueError, match="not found"):
        load_cmapss_run_to_failure(Path("non_existent_file.txt"), "TEST_DS", 10)


def test_loader_wrong_column_count(tmp_path: Path) -> None:
    """Test rejection when column count is not 26."""
    file_path = tmp_path / "bad_cols.txt"
    file_path.write_text("1 1 10.0 20.0 30.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected exactly 26"):
        load_cmapss_run_to_failure(file_path, "TEST_DS", 1)


def test_loader_nan_rejection(tmp_path: Path) -> None:
    """Test rejection when NaN/null values exist."""
    data_str = _make_valid_synthetic_data(num_engines=1, cycles_per_engine=3)
    # Replace one value with NaN
    data_str = data_str.replace("100.0", "NaN")
    file_path = tmp_path / "nan.txt"
    file_path.write_text(data_str, encoding="utf-8")

    with pytest.raises(ValueError, match="null/NaN"):
        load_cmapss_run_to_failure(file_path, "TEST_DS", 1)


def test_loader_inf_rejection(tmp_path: Path) -> None:
    """Test rejection when infinity is present."""
    data_str = _make_valid_synthetic_data(num_engines=1, cycles_per_engine=3)
    data_str = data_str.replace("100.0", "inf")
    file_path = tmp_path / "inf.txt"
    file_path.write_text(data_str, encoding="utf-8")

    with pytest.raises(ValueError, match="infinite values"):
        load_cmapss_run_to_failure(file_path, "TEST_DS", 1)


def test_loader_non_integral_unit(tmp_path: Path) -> None:
    """Test rejection of non-integral unit ID."""
    data_str = _make_valid_synthetic_data(num_engines=1, cycles_per_engine=2)
    # Change unit 1 to 1.5
    lines = data_str.strip().split("\n")
    lines[0] = "1.5 " + " ".join(lines[0].split()[1:])
    file_path = tmp_path / "non_int_unit.txt"
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="non-integral engine IDs"):
        load_cmapss_run_to_failure(file_path, "TEST_DS", 1)


def test_loader_non_integral_cycle(tmp_path: Path) -> None:
    """Test rejection of non-integral cycle ID."""
    data_str = _make_valid_synthetic_data(num_engines=1, cycles_per_engine=2)
    lines = data_str.strip().split("\n")
    tokens = lines[0].split()
    tokens[1] = "1.2"
    lines[0] = " ".join(tokens)
    file_path = tmp_path / "non_int_cycle.txt"
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="non-integral cycle IDs"):
        load_cmapss_run_to_failure(file_path, "TEST_DS", 1)


def test_loader_unit_non_positive(tmp_path: Path) -> None:
    """Test rejection when unit <= 0."""
    data_str = _make_valid_synthetic_data(num_engines=1, cycles_per_engine=2)
    lines = data_str.strip().split("\n")
    tokens = lines[0].split()
    tokens[0] = "0"
    lines[0] = " ".join(tokens)
    file_path = tmp_path / "zero_unit.txt"
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="engine IDs <= 0"):
        load_cmapss_run_to_failure(file_path, "TEST_DS", 1)


def test_loader_cycle_non_positive(tmp_path: Path) -> None:
    """Test rejection when cycle <= 0."""
    data_str = _make_valid_synthetic_data(num_engines=1, cycles_per_engine=2)
    lines = data_str.strip().split("\n")
    tokens = lines[0].split()
    tokens[1] = "0"
    lines[0] = " ".join(tokens)
    file_path = tmp_path / "zero_cycle.txt"
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="cycle IDs <= 0"):
        load_cmapss_run_to_failure(file_path, "TEST_DS", 1)


def test_loader_duplicate_unit_cycle_rejected(tmp_path: Path) -> None:
    """Test rejection of duplicate (unit, cycle) row."""
    data_str = _make_valid_synthetic_data(num_engines=1, cycles_per_engine=2)
    lines = data_str.strip().split("\n")
    # Duplicate first row
    lines.append(lines[0])
    file_path = tmp_path / "dup.txt"
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate"):
        load_cmapss_run_to_failure(file_path, "TEST_DS", 1)


def test_loader_cycle_gap_rejected(tmp_path: Path) -> None:
    """Test rejection when cycle gap exists (e.g. 1, 2, 4)."""
    lines: list[str] = []
    for cycle in [1, 2, 4]:  # Gap at cycle 3
        settings = [10.0, 0.2, 100.0]
        sensors = [1.0] * 21
        row = ["1", str(cycle)] + [str(x) for x in settings] + [str(s) for s in sensors]
        lines.append(" ".join(row))

    file_path = tmp_path / "gap.txt"
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="non-consecutive"):
        load_cmapss_run_to_failure(file_path, "TEST_DS", 1)


def test_loader_trajectory_not_starting_at_1_rejected(tmp_path: Path) -> None:
    """Test rejection when trajectory starts at cycle > 1."""
    lines: list[str] = []
    for cycle in [2, 3, 4]:
        settings = [10.0, 0.2, 100.0]
        sensors = [1.0] * 21
        row = ["1", str(cycle)] + [str(x) for x in settings] + [str(s) for s in sensors]
        lines.append(" ".join(row))

    file_path = tmp_path / "not_start_1.txt"
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="does not start at cycle 1"):
        load_cmapss_run_to_failure(file_path, "TEST_DS", 1)


def test_loader_missing_engine_id_rejected(tmp_path: Path) -> None:
    """Test rejection when an engine ID is missing (e.g. engines 1 and 3, missing 2)."""
    data_1 = _make_valid_synthetic_data(num_engines=1, cycles_per_engine=2)
    # Make engine 3
    lines_3 = []
    for cycle in [1, 2]:
        settings = [10.0, 0.2, 100.0]
        sensors = [1.0] * 21
        row = ["3", str(cycle)] + [str(x) for x in settings] + [str(s) for s in sensors]
        lines_3.append(" ".join(row))

    file_path = tmp_path / "missing_eng.txt"
    file_path.write_text(data_1 + "\n".join(lines_3) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="consecutive 1.."):
        load_cmapss_run_to_failure(file_path, "TEST_DS", expected_engine_count=2)


def test_loader_unexpected_extra_engine_rejected(tmp_path: Path) -> None:
    """Test rejection when extra engine is present."""
    data_str = _make_valid_synthetic_data(num_engines=4, cycles_per_engine=2)
    file_path = tmp_path / "extra_eng.txt"
    file_path.write_text(data_str, encoding="utf-8")

    with pytest.raises(ValueError, match="expected exactly 3"):
        load_cmapss_run_to_failure(file_path, "TEST_DS", expected_engine_count=3)
