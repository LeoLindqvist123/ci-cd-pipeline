"""Quality gate. Run: python -m churn.evaluate [outputs/metrics.json]

Reads metrics from a trained model and exits with error code 1 if ROC AUC
is below the threshold. A step that exits with an error code turns red in
GitHub Actions, stopping jobs that depend on it.

The threshold can be changed using the MIN_ROC_AUC environment variable.
"""

import json
import os
import sys
from pathlib import Path

# Chosen from the baseline and the variance in ROC AUC across random seeds,
# see analysis/seed_variance.py and README "Model Threshold Analysis".
DEFAULT_THRESHOLD = 0.74


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    file_path = Path(argv[0]) if argv else Path("outputs/metrics.json")
    threshold = float(os.environ.get("MIN_ROC_AUC", DEFAULT_THRESHOLD))

    if not file_path.exists():
        print(f"ERROR: Cannot find {file_path}. Has the model been trained or downloaded here?")
        return 1

    metrics = json.loads(file_path.read_text())
    print(json.dumps(metrics, indent=2))

    if metrics["roc_auc"] < threshold:
        print(
            f"ERROR: ROC AUC {metrics['roc_auc']:.3f} is below "
            f"the threshold of {threshold:.2f}."
        )
        return 1
    print(
        f"OK: ROC AUC {metrics['roc_auc']:.3f} meets "
        f"the threshold of {threshold:.2f}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
