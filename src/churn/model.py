"""Model training and evaluation. Run: python -m churn.model

Writes outputs/model.joblib and outputs/metrics.json.
"""

import hashlib
import json
import os
from pathlib import Path

import joblib
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from churn.artifact_integrity import write_checksum
from churn.data import (
    CATEGORICAL_FEATURES,
    DATA_DIR,
    NUMERIC_FEATURES,
    create_features,
    load_data,
    split_features_and_target,
)
from churn.tracking import log_training_run

SEED = 42
TEST_SIZE = 0.25
DATA_FILE = "kundbas.csv"


def build_model() -> Pipeline:
    preprocessing = ColumnTransformer(
        [
            (
                "numeric",
                make_pipeline(
                    SimpleImputer(strategy="median"),
                    StandardScaler(),
                ),
                    NUMERIC_FEATURES,
            ),
            ("categorical",
             OneHotEncoder(handle_unknown="ignore"),
             CATEGORICAL_FEATURES,
            ),
        ]
    )
    return Pipeline(
        [
            ("preprocessing", preprocessing),
            (
                "classifier",
                LogisticRegression(max_iter=1000, random_state=SEED),
            ),
        ]
    )


def train_and_evaluate(
    filename: str = DATA_FILE,
) -> tuple[Pipeline, dict[str, float]]:
    features, target = split_features_and_target(
        create_features(load_data(filename))
    )

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        random_state=SEED,
        stratify=target,
    )

    model = build_model().fit(X_train, y_train)
    probabilities = model.predict_proba(X_test)[:, 1]
    metrics = {
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "accuracy": float(accuracy_score(y_test, model.predict(X_test))
    ),
    }

    # Analyze different classification thresholds
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]

    for threshold in thresholds:
        threshold_predictions = (probabilities >= threshold).astype(int)

        prefix = f"threshold_{threshold:.1f}"

        metrics[f"{prefix}_precision"] = float(
        precision_score(
            y_test,
            threshold_predictions,
            zero_division=0,
            )
        )
        metrics[f"{prefix}_recall"] = float(
        recall_score(y_test,
                threshold_predictions,
                zero_division=0,
             )
        )
        metrics[f"{prefix}_f1"] = float(
            f1_score(
                y_test,
                threshold_predictions,
                zero_division=0,
            )
        )

    return model, metrics


def main(output_dir: Path = Path("outputs")) -> None:
    model, metrics = train_and_evaluate()

    # Track the commit and data file used to produce the model.
    # GITHUB_SHA is available in GitHub Actions; locally, use "local".
    metrics["commit"] = os.environ.get("GITHUB_SHA", "local")
    metrics["data_file"] = DATA_FILE
    metrics["data_sha256"] = hashlib.sha256(
        (DATA_DIR / DATA_FILE).read_bytes()
        ).hexdigest()

    # Log to MLflow if MLFLOW_TRACKING_URI is set (no-op otherwise).
    run_id = log_training_run(
        model,
        metrics,
        params={
            "seed": SEED,
            "test_size": TEST_SIZE,
            "classifier": type(model.named_steps["classifier"]).__name__,
        },
    )

    if run_id is not None:
        metrics["mlflow_run_id"] = run_id

    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / "model.joblib"
    joblib.dump(model, model_path)
    write_checksum(model_path)

    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2)
    )

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
