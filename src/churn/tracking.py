"""Optional MLflow tracking for training runs.

Logging is only active when MLFLOW_TRACKING_URI is set, e.g.:
    MLFLOW_TRACKING_URI=sqlite:///mlflow.db uv run python -m churn.model
Without it, training works exactly as before.
"""

import os

from sklearn.pipeline import Pipeline

EXPERIMENT_NAME = "churn"
REGISTERED_MODEL_NAME = "churn-model"


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

        # skops only loads types it explicitly trusts. numpy.dtype comes from
        # the OneHotEncoder's output dtype and is a plain NumPy data type.
        mlflow.sklearn.log_model(
            model,
            name="model",
            skops_trusted_types=["numpy.dtype"],
        )

        return run.info.run_id


def register_model(run_id: str, alias: str = "champion") -> str | None:
    """Register the model from a run in the Model Registry and set an alias.

    Returns the new model version, or None if tracking is disabled.
    """
    if not tracking_enabled():
        print("MLFLOW_TRACKING_URI is not set, skipping model registration.")
        return None

    import mlflow

    model_version = mlflow.register_model(
        model_uri=f"runs:/{run_id}/model",
        name=REGISTERED_MODEL_NAME,
    )
    mlflow.MlflowClient().set_registered_model_alias(
        name=REGISTERED_MODEL_NAME,
        alias=alias,
        version=model_version.version,
    )

    print(f"Registered {REGISTERED_MODEL_NAME} version {model_version.version} as '{alias}'.")
    return str(model_version.version)
