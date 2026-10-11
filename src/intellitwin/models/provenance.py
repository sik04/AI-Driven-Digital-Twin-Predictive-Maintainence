"""Provenance validation for model selection reporting and frozen split integrity.

Ensures that model selection summaries and reporting metadata conform strictly
to authoritative frozen data manifests, that partition counts derive directly
from manifests rather than unverified prose, and that calibration and held-out test
partitions were not touched.
"""

from dataclasses import dataclass
from typing import Any

from intellitwin.data.splits import SplitManifest, partition_counts


@dataclass(frozen=True)
class SelectionProvenanceReport:
    """Validated model-selection provenance report derived from authoritative sources."""

    dataset: str
    train_count: int
    calibration_count: int
    validation_count: int
    test_count: int
    total_count: int
    calibration_data_used: bool
    test_data_used: bool
    selected_configuration_id: str


def validate_selection_provenance(
    dataset_name: str,
    manifest: SplitManifest,
    selection_summary: dict[str, Any],
) -> SelectionProvenanceReport:
    """Validate model-selection summary metadata against the authoritative split manifest.

    Parameters
    ----------
    dataset_name : str
        Expected dataset name (e.g. 'FD002').
    manifest : SplitManifest
        Authoritative loaded split manifest.
    selection_summary : dict[str, Any]
        Parsed model-selection summary JSON dictionary.

    Returns
    -------
    SelectionProvenanceReport
        Structured provenance report with manifest-derived counts.

    Raises
    ------
    ValueError
        If dataset mismatches, forbidden data roles were used, selection seeds deviate,
        or required artifact provenance fields are missing/empty.
    """
    if manifest.dataset != dataset_name:
        raise ValueError(
            f"Manifest dataset '{manifest.dataset}' does not match expected '{dataset_name}'."
        )

    summary_dataset = selection_summary.get("dataset")
    if summary_dataset != dataset_name:
        raise ValueError(
            f"Selection summary dataset '{summary_dataset}' does not match '{dataset_name}'."
        )

    selection_seeds = selection_summary.get("selection_seeds")
    if selection_seeds != [2026, 2027]:
        raise ValueError(f"Expected selection_seeds to be [2026, 2027], got {selection_seeds}.")

    cal_used = selection_summary.get("calibration_data_used")
    if cal_used is not False:
        raise ValueError(f"calibration_data_used must be False in model selection, got {cal_used}.")

    test_used = selection_summary.get("test_data_used")
    if test_used is not False:
        raise ValueError(f"test_data_used must be False in model selection, got {test_used}.")

    preprocessor_sha = selection_summary.get("preprocessing_artifact_sha256")
    if (
        not preprocessor_sha
        or not isinstance(preprocessor_sha, str)
        or not preprocessor_sha.strip()
    ):
        raise ValueError("Missing or invalid 'preprocessing_artifact_sha256' in selection summary.")

    selected_cfg_id = selection_summary.get("selected_configuration_id")
    if not selected_cfg_id or not isinstance(selected_cfg_id, str) or not selected_cfg_id.strip():
        raise ValueError("Missing or invalid 'selected_configuration_id' in selection summary.")

    counts = partition_counts(manifest)

    return SelectionProvenanceReport(
        dataset=dataset_name,
        train_count=counts["train"],
        calibration_count=counts["calibration"],
        validation_count=counts["validation"],
        test_count=counts["test"],
        total_count=counts["total"],
        calibration_data_used=bool(selection_summary["calibration_data_used"]),
        test_data_used=bool(selection_summary["test_data_used"]),
        selected_configuration_id=selected_cfg_id.strip(),
    )
