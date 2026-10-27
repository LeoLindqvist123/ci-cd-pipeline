"""Compare candidate model performance against an approved baseline."""

import json
import math
import sys
from pathlib import Path

DEFAULT_METRICS_PATH = Path("outputs/metrics.json")
DEFAULT_BASELINE_PATH = Path("config/model_baseline.json")

# Maximum acceptable decrease in ROC AUC compared with the baseline.
MAX_ROC_AUC_DROP = 0.02


def read_roc_auc(file_path: Path) -> float:
    """Read and validate the ROC AUC value from a JSON file."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")

    data = json.loads(file_path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {file_path}")

    score = data.get("roc_auc")

    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not math.isfinite(score)
        or not 0 <= score <= 1
    ):
        raise ValueError(
            f"Invalid or missing ROC AUC value in {file_path}"
        )

    return float(score)


def main(argv: list[str] | None = None) -> int:
    """Return 1 if the candidate model regresses beyond the allowed limit."""
    argv = sys.argv[1:] if argv is None else argv

    if len(argv) > 2:
        print(
            "Usage: python -m churn.regression_gate "
            "[METRICS_PATH] [BASELINE_PATH]",
            file=sys.stderr,
        )
        return 2

    metrics_path = (
        Path(argv[0]) if argv else DEFAULT_METRICS_PATH
    )
    baseline_path = (
        Path(argv[1]) if len(argv) > 1 else DEFAULT_BASELINE_PATH
    )

    try:
        candidate_auc = read_roc_auc(metrics_path)
        baseline_auc = read_roc_auc(baseline_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    minimum_auc = baseline_auc - MAX_ROC_AUC_DROP
    actual_drop = baseline_auc - candidate_auc

    print(f"Baseline ROC AUC: {baseline_auc:.3f}")
    print(f"Candidate ROC AUC: {candidate_auc:.3f}")
    print(f"Minimum acceptable ROC AUC: {minimum_auc:.3f}")

    # Allow a tiny floating-point tolerance at the boundary.
    if actual_drop > MAX_ROC_AUC_DROP + 1e-12:
        print(
            f"ERROR: Model regression of {actual_drop:.3f} "
            f"exceeds the allowed drop of {MAX_ROC_AUC_DROP:.3f}."
        )
        return 1

    print("OK: Candidate model passes the regression gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
