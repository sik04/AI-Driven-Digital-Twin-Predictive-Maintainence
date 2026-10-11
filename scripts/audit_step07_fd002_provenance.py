"""Deterministic Step 7.3 FD002 model-selection provenance audit script.

Verifies that FD002 model-selection summary artifacts conform strictly to the
authoritative frozen split manifest (data/splits/fd002_engine_split_seed_2026.json),
verifies that partition counts match the frozen protocol (Train 130, Calibration 52,
Validation 26, Test 52, Total 260), confirms calibration and held-out test data
were not touched, and asserts the frozen winning configuration IDs.

Exits with code 0 on PASS, or code 1 on failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from intellitwin.data.splits import load_split_manifest
from intellitwin.models.provenance import validate_selection_provenance

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "data" / "splits" / "fd002_engine_split_seed_2026.json"
GBR_SELECTION_PATH = REPO_ROOT / "experiments" / "model_selection" / "FD002" / "gbr_selection.json"
LSTM_SELECTION_PATH = (
    REPO_ROOT / "experiments" / "model_selection" / "FD002" / "lstm_selection.json"
)

EXPECTED_COUNTS = {
    "train": 130,
    "calibration": 52,
    "validation": 26,
    "test": 52,
    "total": 260,
}
EXPECTED_GBR_WINNER = "gbr_lr010_leaf31_l2_0"
EXPECTED_LSTM_WINNER = "lstm_h64_lr0010"


def audit_fd002_provenance() -> int:
    """Run the Step 7.3 FD002 provenance audit.

    Returns
    -------
    int
        Exit code (0 for success, 1 for failure).
    """
    if not MANIFEST_PATH.is_file():
        print(f"ERROR: Split manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    if not GBR_SELECTION_PATH.is_file():
        print(f"ERROR: GBR selection summary not found: {GBR_SELECTION_PATH}", file=sys.stderr)
        return 1

    if not LSTM_SELECTION_PATH.is_file():
        print(f"ERROR: LSTM selection summary not found: {LSTM_SELECTION_PATH}", file=sys.stderr)
        return 1

    try:
        manifest = load_split_manifest(MANIFEST_PATH)
        with open(GBR_SELECTION_PATH, encoding="utf-8") as f:
            gbr_summary = json.load(f)
        with open(LSTM_SELECTION_PATH, encoding="utf-8") as f:
            lstm_summary = json.load(f)

        gbr_report = validate_selection_provenance("FD002", manifest, gbr_summary)
        lstm_report = validate_selection_provenance("FD002", manifest, lstm_summary)

        # Verify manifest-derived partition counts
        for partition_key, expected_val in EXPECTED_COUNTS.items():
            actual_val = getattr(gbr_report, f"{partition_key}_count")
            if actual_val != expected_val:
                msg = (
                    f"Partition '{partition_key}' count mismatch: "
                    f"expected {expected_val}, got {actual_val}."
                )
                raise ValueError(msg)

        # Verify winning configuration IDs
        if gbr_report.selected_configuration_id != EXPECTED_GBR_WINNER:
            msg = (
                f"GBR winner mismatch: expected '{EXPECTED_GBR_WINNER}', "
                f"got '{gbr_report.selected_configuration_id}'."
            )
            raise ValueError(msg)
        if lstm_report.selected_configuration_id != EXPECTED_LSTM_WINNER:
            msg = (
                f"LSTM winner mismatch: expected '{EXPECTED_LSTM_WINNER}', "
                f"got '{lstm_report.selected_configuration_id}'."
            )
            raise ValueError(msg)

        # Verify calibration and test data untouched
        if gbr_report.calibration_data_used or lstm_report.calibration_data_used:
            raise ValueError("Calibration data was used during model selection.")
        if gbr_report.test_data_used or lstm_report.test_data_used:
            raise ValueError("Held-out test data was used during model selection.")

    except Exception as exc:
        print(f"FD002 provenance audit: FAIL - {exc}", file=sys.stderr)
        return 1

    print("FD002 provenance audit: PASS")
    print(
        f"Partition counts: Train {gbr_report.train_count} "
        f"Calibration {gbr_report.calibration_count} "
        f"Validation {gbr_report.validation_count} "
        f"Test {gbr_report.test_count} "
        f"Total {gbr_report.total_count}"
    )
    print(f"GBR winner: {gbr_report.selected_configuration_id}")
    print(f"LSTM winner: {lstm_report.selected_configuration_id}")
    print("Calibration data used: NO")
    print("Held-out test data used: NO")

    return 0


if __name__ == "__main__":
    sys.exit(audit_fd002_provenance())
