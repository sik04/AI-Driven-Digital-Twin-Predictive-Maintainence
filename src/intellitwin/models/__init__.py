"""Point-RUL base predictors, evaluation metrics, and selection framework.

Adheres strictly to ADR-019 and Step 7.1 specification:
- GBR: HistGradientBoostingRegressor (8 frozen configurations).
- LSTM: Single-layer unidirectional LSTM (4 frozen configurations).
- Equal-engine-weighted metrics (uncapped RMSE, uncapped MAE, capped RMSE).
- Reproducible deterministic execution across CPU/CUDA.
- Deterministic candidate ranking and tie-breaking.
"""

from intellitwin.models.artifacts import (
    save_prediction_artifact,
    save_run_record,
    save_selection_summary,
)
from intellitwin.models.gbr import (
    GBR_GRID,
    GBRHyperparameters,
    GBRModel,
    get_gbr_grid,
)
from intellitwin.models.lstm import (
    LSTM_GRID,
    LSTMHyperparameters,
    LSTMPointPredictor,
    LSTMTrainingResult,
    get_lstm_grid,
    load_lstm_checkpoint,
    save_lstm_checkpoint,
    train_lstm_candidate,
)
from intellitwin.models.metrics import (
    ModelEvaluationMetrics,
    compute_model_metrics,
)
from intellitwin.models.provenance import (
    SelectionProvenanceReport,
    validate_selection_provenance,
)
from intellitwin.models.registry import (
    FrozenBaseModel,
    load_frozen_base_model,
)
from intellitwin.models.reproducibility import (
    resolve_device,
    set_global_seed,
)
from intellitwin.models.selection import (
    SELECTION_SEEDS,
    CandidateEvaluationResult,
    SelectionOutcome,
    evaluate_candidate,
    select_best_configuration,
)

__all__ = [
    "GBR_GRID",
    "GBRHyperparameters",
    "GBRModel",
    "FrozenBaseModel",
    "LSTM_GRID",
    "LSTMHyperparameters",
    "LSTMPointPredictor",
    "LSTMTrainingResult",
    "ModelEvaluationMetrics",
    "SELECTION_SEEDS",
    "CandidateEvaluationResult",
    "SelectionOutcome",
    "SelectionProvenanceReport",
    "compute_model_metrics",
    "evaluate_candidate",
    "get_gbr_grid",
    "get_lstm_grid",
    "load_frozen_base_model",
    "load_lstm_checkpoint",
    "resolve_device",
    "save_lstm_checkpoint",
    "save_prediction_artifact",
    "save_run_record",
    "save_selection_summary",
    "select_best_configuration",
    "set_global_seed",
    "train_lstm_candidate",
    "validate_selection_provenance",
]
