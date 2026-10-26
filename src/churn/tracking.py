"""Optional MLflow tracking for training runs.

Logging is only active when MLFLOW_TRACKING_URI is set, e.g.:
    MLFLOW_TRACKING_URI=sqlite:///mlflow.db uv run python -m churn.model
Without it, training works exaclty as before.
"""

import os

from sklearn.pipeline import Pipeline

EXPERIMENT_NAME = "churn"


def tracking_enabled() -> bool:
    """Return True if an MLflow tracking URI is configured."""
    return bool(os.environ.get("MLFLOW_TRACKING_URI"))


def log_training_run(
        model: Pipeline,
        metrics: dict,
        params: dict,
    ) -> str | None:
    """Log params, metrics, lineage tags and the model to MLflow.

    Returns the MLflow run id, or None if tracking is disabled.
    """
    if not tracking_enabled():
        print("MLFLOW_TRACKING_URI is not set, skipping MLflow logging.")
        return None


    # Imported here so the package still works without the 'tracking' extra.
    import mlflow
    import mlflow.sklearn

    mlflow.set_experiment(EXPERIMENT_NAME)

    commit = str(metrics.get("commit", "local"))

    with mlflow.start_run(run_name=f"train-{commit[:7]}") as run:
        mlflow.set_tags(
            {
                "commit": commit,
                "data_file": str(metrics.get("data_file", "unknown")),
                "data_sha256": str(metrics.get("data_sha256", "unknown")),
            }
        )

        mlflow.log_params(params)

        numeric_metrics = {
            key: value
            for key, value in metrics.items()
            if isinstance(value, int | float)
        }
        mlflow.log_metrics(numeric_metrics)

        mlflow.sklearn.log_model(
            model,
            name="model",
            skops_trusted_types=["numpy.dtype"]
        )

        return run.info.run_id

