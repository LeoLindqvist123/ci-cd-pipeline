# CI/CD - Pipeline

This repository contains the MLOps pipeline for predicting [customer churn for Saldes Mobil AB](https://github.com/saldes-education/saldes-mobil-churn).
It includes data validation, model training, and an automated CI/CD pipeline.

## 🚀 Quick Start (Local Setup)

This project uses `uv` for lightning-fast dependency management. To set up your local environment:

1. Clone the repository:
   ```bash
   git clone https://github.com/LeoLindqvist123/ci-cd-pipeline.git
   cd ci-cd-pipeline
   ```
2. Sync the environment and install all dependencies (including dev and data tools):
   ```bash
   uv sync --all-extras
   ```
3. Run your tests or scripts directly using `uv run`:

```bash
#Example run command
uv run pytest

uv run python src/churn/some_script.py
```

## ✅ Data Validation

The data is validated against a Pandera schema (`kontroll/schema.py`) in CI. To run it locally:

```bash
uv run python kontroll/schema.py [path/to/file.csv]
```
If no file is given, `data/kundbas.csv` is used. For example, to validate a new delivery:

```bash
uv run python kontroll/schema.py data/kundbas_ny_leverans.csv
```

If validation fails, the script lists errors per column and check with a few examples, and exits with code 1, which fails the CI pipeline.

## 📊 Model Threshold Analysis

The pipeline needs a minimum ROC AUC for the model to pass CI. To choose that
threshold from data instead of guessing, we measured how much ROC AUC varies
with the random seed alone.

### What the script does

`analysis/seed_variance.py` trains and evaluates the model 30 times, with seeds 0–29. The data, features and model stay the same. 
Only `SEED` in `churn.model` changes, and it controls the train/test split. Each run therefore evaluates on a different 25 % of the customers.

```bash
uv run python analysis/seed_variance.py
```

### Results (`kundbas.csv`, 30 seeds)

| Statistic          | ROC AUC |
|--------------------|---------|
| Min                | 0.746   |
| Max                | 0.836   |
| Mean               | 0.783   |
| Standard deviation | 0.020   |
| Pipeline (seed 42) | 0.789   |

Seed 42 is close to the mean. The pipeline's fixed seed is therefore representative and not an unusually lucky split.

### Candidate thresholds

All 30 runs use the same data and the same model. They differ only in which
customers end up in the test set. The spread in ROC AUC (0.746 to 0.836) therefore
shows how much the score can vary from the split alone, without any change to the model.

This affects where the threshold can go:

- **Inside the spread:** CI may fail a model simply because of an unlucky split.
- **Far below the spread:** CI may let a model pass even after it has actually got worse.

The table shows how many of the 30 runs would have failed CI with each candidate
threshold. A run fails if its ROC AUC is below the threshold. Since the model was
unchanged between runs, these failures are likely caused by variation in the
train/test split rather than by a worse model. The analysis shows that this
variation exists, but it cannot prove that every future failure has this cause.

| Candidate                    | Threshold | Runs that would fail |
|------------------------------|-----------|----------------------|
| Mean − 1 standard deviation  | 0.763     | 5 / 30               |
| 10th percentile              | 0.760     | 3 / 30               |
| 5th percentile               | 0.751     | 2 / 30               |
| Lowest observed score        | 0.746     | 0 / 30               |
| Mean − 2 standard deviations | 0.743     | 0 / 30               |
| Mean − 3 standard deviations | 0.724     | 0 / 30               |

A lower threshold gives fewer failures caused by the split. The cost is that the
model's quality has to drop more before CI catches it.

### Decision

The CI threshold is set to **ROC AUC ≥ 0.74**, roughly the mean minus two standard deviations.

Motivation:

- **No failures in the analysis.** The threshold is below the lowest observed score (0.746), so none of the 30 runs would have failed CI because of the split alone.
- **Still catches real degradation.** It is only about 0.05 below the pipeline's score (0.789). A clearly worse model would still fail CI.
- **Standard choice.** Mean − 2 SD is a common rule of thumb, while mean − 3 SD (0.724) would let too large a drop through.

The threshold should be revisited if the data, features or model change significantly. In that case, rerun `analysis/seed_variance.py`.

## 📁 Project Structure

```text
ci-cd-pipeline/
├── .github/
│   ├── actions/
│   │   └── setup-project/
│   │       └── action.yml
│   └── workflows/
│       └── ci.yml
├── analysis/
│   └── seed_variance.py
├── data/
│   ├── kundbas.csv
│   └── kundbas_ny_leverans.csv
├── kontroll/
│   └── schema.py
├── src/
│   └── churn/
├── tests/
│   ├── demo_datagrind.py
│   ├── test_data.py
│   ├── test_features.py
│   └── test_model.py
├── create_issues.py
├── issues.json
├── .gitignore
├── pyproject.toml
├── README.md
└── uv.lock
```

## 🛠️ Development Roadmap & Task Status

*(Team: Please update the status of your assigned tasks below when you merge your PR!)*

### 1. Infrastructure & Setup
- [x] Create project board and generate backlog issues
- [x] Migrate dependency management to `uv` and generate lockfile
- [ ] Clean up and finalize README structure

### 2. CI/CD & Testing
- [x] Set up CI pipeline for code quality (Linting/Formatting)
- [x] Create Pandera schema for data validation
- [x] Set up CI pipeline for Pandera data validation tests
- [x] Set up CI pipeline for model training and unit tests

### 3. Machine Learning
- [ ] Analyze model thresholds and document findings
- [ ] Refine feature engineering pipeline

## 👥 Collaborators

This project is collaboratively developed by:
* [Lilit Ajoyan](https://github.com/LAjoyan)
* [Erfan Tahmasebi](https://github.com/erfantk25-lab)
* [Leo Lindqvist Kröhnert](https://github.com/LeoLindqvist123)
* [Josefin Lesley](https://github.com/Josefin3647)