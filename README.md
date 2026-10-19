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
- [ ] Set up CI pipeline for code quality (Linting/Formatting)
- [ ] Create Pandera schema for data validation
- [ ] Set up CI pipeline for Pandera data validation tests
- [ ] Set up CI pipeline for model training and unit tests

### 3. Machine Learning
- [ ] Analyze model thresholds and document findings
- [ ] Refine feature engineering pipeline

## 👥 Collaborators

This project is collaboratively developed by:
* [Lilit Ajoyan](https://github.com/LAjoyan)
* [Erfan Tahmasebi](https://github.com/erfantk25-lab)
* [Leo Lindqvist Kröhnert](https://github.com/LeoLindqvist123)
* [Josefin Lesley](https://github.com/Josefin3647)