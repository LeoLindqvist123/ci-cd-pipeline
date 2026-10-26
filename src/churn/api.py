
"""FastAPI service for the customer churn prediction model."""

import os
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sklearn.pipeline import Pipeline

from churn.data import FEATURES, create_features

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "outputs" / "model.joblib"

MODEL_PATH = Path(
    os.getenv("CHURN_MODEL_PATH", str(DEFAULT_MODEL_PATH))
)

app = FastAPI(
    title="Customer Churn Prediction API",
    description="Predict customer churn using a trained machine learning model.",
    version="1.0.0",
)

_model: Pipeline | None = None


class CustomerInput(BaseModel):
    """Customer information required to predict churn."""

    age: int = Field(ge=18, le=100)
    months_as_customer: int = Field(ge=0)
    monthly_cost: float = Field(gt=0)
    data_gb_per_month: float = Field(ge=0)
    support_tickets_12m: int = Field(ge=0)
    region: str = Field(min_length=1)
    subscription: str = Field(min_length=1)


def get_model() -> Pipeline:
    """Load the trained model when it is first needed."""
    global _model

    if _model is None:
        if not MODEL_PATH.is_file():
            raise HTTPException(
                status_code=503,
                detail="The trained model is unavailable. Train the model first.",
            )

        try:
            _model = joblib.load(MODEL_PATH)
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="The trained model could not be loaded.",
            ) from exc

    return _model


@app.get("/health")
def health() -> dict[str, str | bool]:
    """Check whether the trained model is available."""
    get_model()
    return {"status": "ok", "model_loaded": True}


@app.post("/predict")
def predict(customer: CustomerInput) -> dict[str, int | float]:
    """Predict whether a customer is likely to churn."""
    model = get_model()

    # Map the English API fields to the existing training-data columns.
    customer_data = {
        "alder": customer.age,
        "manader_som_kund": customer.months_as_customer,
        "manadskostnad": customer.monthly_cost,
        "data_gb_per_manad": customer.data_gb_per_month,
        "supportarenden_12m": customer.support_tickets_12m,
        "region": customer.region,
        "abonnemang": customer.subscription,
    }

    customer_df = pd.DataFrame([customer_data])

    # Use the same feature engineering as the training pipeline.
    customer_df = create_features(customer_df)
    features = customer_df[FEATURES]

    prediction = int(model.predict(features)[0])
    churn_probability = float(model.predict_proba(features)[0, 1])

    return {
        "prediction": prediction,
        "churn_probability": round(churn_probability, 6),
    }
