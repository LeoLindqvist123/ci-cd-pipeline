"""Customer service call list. Run: python -m churn.score [outputs/model.joblib]

Calculates the risk for all customers who have not yet left and writes the
highest-risk customers to outputs/call_list.csv. The number is controlled
by the ANTAL environment variable (default: 100).
"""

import os
import sys
from pathlib import Path

import joblib

from churn.data import TARGET, create_features, load_data, split_features_and_target


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    model_path = Path(argv[0]) if argv else Path("outputs/model.joblib")
    limit = int(os.environ.get("ANTAL", 100))

    if not model_path.exists():
        print(f"ERROR: Cannot find {model_path}. "
            "Has the model been trained or downloaded here?")
        return 1

    model = joblib.load(model_path)
    customers = create_features(load_data())
    remaining_customers = customers[customers[TARGET] == 0]
    features, _ = split_features_and_target(remaining_customers)

    call_list = remaining_customers[["kund_id"]].assign(
        risk=model.predict_proba(features)[:, 1].round(3)
        )
    call_list = call_list.sort_values("risk", ascending=False,).head(limit)

    output_file = Path("outputs/call_list.csv")
    output_file.parent.mkdir(exist_ok=True)
    call_list.to_csv(output_file, index=False)
    print(f"Wrote {len(call_list)} customers to {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
