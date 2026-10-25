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


## FastAPI

The API predicts customer churn using the trained model.

Start the API:

```bash
uv run uvicorn churn.api:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to test the endpoints.

- `GET /health` — checks model availability.
- `POST /predict` — returns a churn prediction and probability.

Run API tests:

```bash
uv run pytest tests/test_api.py
```


## ✅ Data Validation

The data is validated against a Pandera schema (`validation/schema.py`) in CI. To run it locally:

```bash
uv run python validation/schema.py [path/to/file.csv]
```
If no file is given, `data/kundbas.csv` is used. For example, to validate a new delivery:

```bash
uv run python validation/schema.py data/kundbas_ny_leverans.csv
```

If validation fails, the script lists errors per column and check with a few examples, and exits with code 1, which fails the CI pipeline.

In CI, the `validate` job checks both data files in parallel:

- `kundbas.csv` must **pass**.
- `kundbas_ny_leverans.csv` must **fail**. It is a known-bad delivery that proves the schema catches errors.

The validation output is shown in the job summary on GitHub. The model is only trained if both checks are green.

## 📊 Classification Threshold Analysis

The churn model predicts the probability that a customer will leave the company. We evaluate different classification thresholds to understand how they affect the model's predictions.

### What the code does

The function `train_and_evaluate()` in `src/churn/model.py` evaluates five classification thresholds: 0.3, 0.4, 0.5, 0.6, and 0.7.

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

The evaluation results, including the new threshold-specific metrics, are printed and saved to `outputs/metrics.json`.

### Why it matters

A lower classification threshold may identify more customers who will churn, but it may also produce more false positives. A higher threshold may reduce false positives while missing more actual churners.

Comparing precision, recall, and F1-score helps the team understand these trade-offs before choosing a classification threshold.

The results from different thresholds should be reviewed before selecting a final threshold. For a more rigorous evaluation, select the threshold using validation data and reserve the test data for the final evaluation.

**Note:** Classification thresholds determine how predicted probabilities are converted into churn predictions. They are different from the minimum ROC AUC threshold used by CI to decide whether model evaluation passes or fails.
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

## 📦 Model Versioning & Lineage

Every model that passes the CI quality gate is versioned as a traceable artifact linked to the exact code commit and dataset that produced it.

### How it works
1. **Metadata & Lineage Generation (`src/churn/model.py`):**
   When `uv run python -m churn.model` runs, it generates both the trained model (`outputs/model.joblib`) and a metadata file (`outputs/metrics.json`) containing:
   - **Evaluation metrics:** `roc_auc`, `accuracy`, and threshold-specific metrics (`precision`, `recall`, `f1`).
   - **Commit traceability:** `commit` (populated from `GITHUB_SHA` in GitHub Actions, or `"local"` when run locally).
   - **Data traceability:** `data_file` (`kundbas.csv`) and `data_sha256` (a 64-character SHA-256 hash of the dataset's exact contents).

2. **Gated Versioning in CI (`.github/workflows/ci.yml`):**
   - The `train` job uploads a temporary candidate artifact (`model-candidate-<sha>`, `retention-days: 1`).
   - The `evaluate` job downloads the candidate, writes the metrics and lineage table to the GitHub Actions **Job Summary**, and runs `uv run python -m churn.evaluate`.
   - **Only if the model passes the quality threshold** (`ROC AUC >= 0.74`) does CI publish the official versioned artifact `model-<sha>`.

3. **Automated Lineage Testing (`tests/test_model.py`):**
   The test `test_model_versioning_metadata` verifies that `model.joblib` and `metrics.json` are created with valid `commit`, `data_file`, `data_sha256`, and evaluation metric fields:

   ```bash
   uv run pytest tests/test_model.py
   ```

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
├── validation/
│   └── schema.py
├── docs/
│   ├── fastapi_prediction_prompt.png
│   └── fastapi_prediction_response.png
├── outputs/
│   ├── model.joblib
│   ├── metrics.json
│   └── call_list.csv
├── src/
│   └── churn/
│         ├── __init__.py
│         ├── api.py
│         ├── data.py
│         ├── evaluate.py
│         ├── model.py
│         └── score.py
├── tests/
│   ├── test_api.py
│   ├── test_data.py
│   ├── test_features.py
│   └── test_model.py
├── create_issues.py
├── issues_followup.json
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

### 2. CI/CD & Testing
- [x] Verify branch protection and required status checks
- [x] Set up CI pipeline for code quality (Linting/Formatting)
- [x] Create Pandera schema for data validation
- [x] Set up CI pipeline for Pandera data validation tests
- [x] Set up CI pipeline for model training and unit tests
- [ ] Verify that invalid data blocks training in the actual pipeline

### 3. Machine Learning
- [ ] Analyze model thresholds and document findings
- [ ] Refine feature engineering pipeline
- [ ] Version approved model artifacts with commit and data metadata
- [ ] Verify that failing model evaluation prevents publication

### 4. Model Serving & FastAPI

- [ ] Add FastAPI prediction endpoint (`POST /predict`)
- [ ] Add health endpoint (`GET /health`)
- [ ] Add automated API tests
- [ ] Document how to run and test the API locally

### 5. Docker & Artifact Publishing

- [ ] Create Dockerfile for the model-serving application
- [ ] Build and run the Docker image
- [ ] Add a container smoke test
- [ ] Push verified images to GitHub Container Registry (GHCR)
- [ ] Tag published images with the relevant commit SHA

### 6. Documentation & Final Verification

- [ ] Update README to reflect the completed pipeline
- [ ] Capture a successful end-to-end pipeline run
- [ ] Capture a run where invalid data stops validation
- [ ] Prepare final repository, commit and PR/review links for submission

## 👥 Collaborators

This project is collaboratively developed by:
* [Lilit Ajoyan](https://github.com/LAjoyan)
* [Erfan Tahmasebi](https://github.com/erfantk25-lab)
* [Leo Lindqvist Kröhnert](https://github.com/LeoLindqvist123)
* [Josefin Lesley](https://github.com/Josefin3647)