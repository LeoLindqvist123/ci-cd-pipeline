import sys

import pandas as pd
import pandera.pandas as pa

SCHEMA = pa.DataFrameSchema(
    {
        "kund_id": pa.Column(int, unique=True),
        "alder": pa.Column(int, pa.Check.in_range(18, 100)),
        "region": pa.Column(str),
        "abonnemang": pa.Column(str),
        "manader_som_kund": pa.Column(int, pa.Check.ge(0)),
        "manadskostnad": pa.Column(float, pa.Check.gt(0)),
        "data_gb_per_manad": pa.Column(float, pa.Check.ge(0)),
        "supportarenden_12m": pa.Column(int, pa.Check.ge(0)),
        "avslutat": pa.Column(int, pa.Check.isin([0, 1])),
    },
    strict=True,
)

datafile = sys.argv[1] if len(sys.argv) > 1 else "data/kundbas.csv"
print(f"Validating {datafile}")

df = pd.read_csv(datafile)
df = df.rename(columns={"manadsavgift": "manadskostnad"})

try:
    SCHEMA.validate(df, lazy=True)
    print("Validation OK")
except pa.errors.SchemaErrors as exc:
    errors = exc.failure_cases.fillna({"column": "<schema>"})

    print(f"Validation failed: {len(errors)} errors\n")
    print("=== Errors per column and check ===")
    print(errors.groupby(["column", "check"]).size().to_string())
    print("\n=== Examples per column/check ===")
    examples = errors.groupby(["column", "check"]).head(3).sort_values(["column", "check"])
    print(examples[["column", "check", "failure_case", "index"]].to_string(index=False))
    sys.exit(1)
