"""Evaluate how stable the churn model's ROC AUC is across different random seeds."""

from statistics import mean, stdev

import churn.model

DATAFILE = "kundbas.csv"
SEEDS = range(30)  # Seeds used to measure the variation
REFERENCE_SEED = 42  # Seed used in the regular pipeline


roc_auc = []
for seed in SEEDS:
    # Override the module-global SEED in churn.model (no seed argument exists)
    churn.model.SEED = seed
    _, metrics = churn.model.trana_och_utvardera(filnamn=DATAFILE)
    roc_auc.append(metrics["roc_auc"])

print(f"\nROC AUC for {len(SEEDS)} seeds:")
print("-" * 34)
print(f"Min: {min(roc_auc):.3f}")
print(f"Max: {max(roc_auc):.3f}")
print(f"Mean: {mean(roc_auc):.3f}")
print(f"Std deviation: {stdev(roc_auc):.3f}")

# Restore the pipeline's reference seed
churn.model.SEED = REFERENCE_SEED
_, metrics = churn.model.trana_och_utvardera(filnamn=DATAFILE)
print("\nROC AUC for pipeline: ")
print("-" * 34)
print(f"Seed {REFERENCE_SEED}: {metrics['roc_auc']:.3f}")
