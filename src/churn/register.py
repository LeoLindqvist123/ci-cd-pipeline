"""Model registration. Run: python -m churn.register [outputs/metrics.json]

Reads the MLflow run id from metrics.json (written by churn.model) and
registers that run's model in the MLflow Model Registry with the alias
"champion". Run it only after churn.evaluate has passed the quality gate.
"""

import json
import sys
from pathlib import Path

from churn.tracking import register_model


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    file_path = Path(argv[0]) if argv else Path("outputs/metrics.json")

    if not file_path.exists():
        print(f"ERROR: Cannot find {file_path}. Has the model been trained or downloaded here?")
        return 1

    metrics = json.loads(file_path.read_text())
    run_id = metrics.get("mlflow_run_id")

    if run_id is None:
        print(
            "ERROR: metrics.json has no mlflow_run_id. "
            "Was the model trained with MLFLOW_TRACKING_URI set?"
        )
        return 1

    if register_model(run_id) is None:
        print("ERROR: The model was not registered. Is MLFLOW_TRACKING_URI set?")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
