"""Step 7.5: Independent Base Predictor Audit Script.

Performs exhaustive verification of:
1. 30-model registry (experiments/base_models/model_registry.json).
2. Exactly 3 datasets x 2 families x 5 seeds = 30 unique cells.
3. Configuration freeze across seeds for every dataset/family cell.
4. Preprocessing artifact SHA-256 constancy and match with committed preprocessors.
5. Split manifest SHA-256 constancy and match with committed split manifests.
6. Checkpoint loadability and numerical reproduction on CPU.
7. Validation prediction endpoint completeness (cycles 30..T for each engine).
8. Target semantics (capped rul_target 125 for training, uncapped rul_true for validation).
9. Strict absence of calibration and test artifacts under experiments/.
"""

import sys
from pathlib import Path

from intellitwin.models.registry import audit_base_model_registry


def main() -> None:
    print("=" * 80)
    print("Step 7.5: Authoritative 30-Model Base Predictor Matrix Audit")
    print("=" * 80)

    registry_path = Path("experiments/base_models/model_registry.json")
    if not registry_path.exists():
        print(f"FAILED: Registry file not found: {registry_path}")
        sys.exit(1)

    try:
        results = audit_base_model_registry(
            registry_path=registry_path,
            base_dir=Path("."),
            reload_checkpoints=True,
        )
    except Exception as exc:
        print(f"\nAUDIT FAILED with exception:\n{exc}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("AUDIT RESULT: ALL CHECKS PASSED (STATUS: PASS)")
    print(f"Total verified models: {results['models_audited']}/30")
    print(f"Datasets: {results['datasets']}")
    print(f"Families: {results['families']}")
    print(f"Seeds: {results['seeds']}")
    print("Configurations:")
    for cell, cfg_id in results["configurations"].items():
        print(f"  {cell:12s}: {cfg_id}")
    print("=" * 80)


if __name__ == "__main__":
    main()
