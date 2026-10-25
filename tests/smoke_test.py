"""Smoke test for the containerized churn prediction API.

Can be run against a locally running Docker container or directly in CI.
Usage:
    python tests/smoke_test.py [BASE_URL]
Default BASE_URL is http://localhost:8000
"""

import json
import sys
import time
import urllib.error
import urllib.request


def wait_for_service(url: str, timeout_seconds: int = 30) -> bool:
    """Poll GET /health until the service is ready or timeout expires."""
    health_url = f"{url}/health"
    start_time = time.time()
    print(f"Waiting for service to become healthy at {health_url}...")

    while time.time() - start_time < timeout_seconds:
        try:
            with urllib.request.urlopen(health_url, timeout=2) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    if data.get("status") == "ok" and data.get("model_loaded") is True:
                        print("Service is up and model is loaded successfully!")
                        return True
        except (urllib.error.URLError, ConnectionError):
            time.sleep(1)

    print(f"ERROR: Service failed to respond within {timeout_seconds} seconds.")
    return False


def verify_predict_endpoint(url: str) -> bool:
    """Verify that POST /predict accepts input and returns a valid churn prediction."""
    predict_url = f"{url}/predict"
    payload = {
        "age": 42,
        "months_as_customer": 12,
        "monthly_cost": 299.0,
        "data_gb_per_month": 15.5,
        "support_tickets_12m": 1,
        "region": "Väst",
        "subscription": "Standard",
    }
    req = urllib.request.Request(
        predict_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                print(f"ERROR: /predict returned HTTP status {response.status}")
                return False

            res_data = json.loads(response.read().decode())
            print(f"Prediction response: {res_data}")

            if "prediction" not in res_data or "churn_probability" not in res_data:
                print("ERROR: Response missing required fields (prediction or probability)")
                return False

            prediction = res_data["prediction"]
            probability = res_data["churn_probability"]

            if prediction not in (0, 1):
                print(f"ERROR: Invalid prediction value: {prediction} (expected 0 or 1)")
                return False

            if not (0.0 <= probability <= 1.0):
                print(f"ERROR: Probability out of bounds: {probability}")
                return False

            print("Smoke test PASSED: Prediction output verified successfully.")
            return True

    except Exception as exc:
        print(f"ERROR: Request to {predict_url} failed: {exc}")
        return False


def main() -> int:
    base_url = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
    print(f"--- Running Container Smoke Test against: {base_url} ---")

    if not wait_for_service(base_url, timeout_seconds=30):
        return 1

    if not verify_predict_endpoint(base_url):
        return 1

    print("--- Smoke Test Completed Successfully! ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
