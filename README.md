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

```Bash
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

In CI, the `validate` job checks both data files in parallel:
- `kundbas.csv` must **pass**.
- `kundbas_ny_leverans.csv` must **fail**. It is a known-bad delivery that proves the schema catches errors.

The validation output is shown in the job summary on GitHub. The model is only trained if both checks are green.

## 📊 Classification Threshold Analysis

The churn model predicts the probability that a customer will leave the company. We evaluate different classification thresholds to understand how they affect the model's predictions.

### What the code does

The function `trana_och_utvardera()` in `src/churn/model.py` evaluates five classification thresholds: 0.3, 0.4, 0.5, 0.6, and 0.7.

For each threshold, a customer is classified as likely to churn if their predicted probability is greater than or equal to that threshold.

The model calculates three additional metrics for each threshold:

- **Precision:** Of the customers predicted to churn, how many actually churned?
- **Recall:** Of all customers who actually churned, how many did the model identify?
- **F1-score:** A combined measure of precision and recall.

The existing ROC AUC and accuracy metrics are retained.

### How to run

Run the model training and evaluation module:

```bash
uv run python -m churn.model
```

The evaluation results, including the new threshold-specific metrics, are printed and saved to `outputs/matvarden.json`.

### Why it matters

A lower classification threshold may identify more customers who will churn, but it may also produce more false positives. A higher threshold may reduce false positives while missing more actual churners.

Comparing precision, recall, and F1-score helps the team understand these trade-offs before choosing a classification threshold.

The results from different thresholds should be reviewed before selecting a final threshold. For a more rigorous evaluation, select the threshold using validation data and reserve the test data for the final evaluation.

**Note:** Classification thresholds determine how predicted probabilities are converted into churn predictions. They are different from the minimum ROC AUC threshold used by CI to decide whether model evaluation passes or fails.

## 📁 Project Structure

```text
ci-cd-pipeline/
├── .github/
│   ├── actions/
│   │   └── setup-project/
│   │       └── action.yml
│   └── workflows/
│       └── ci.yml
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