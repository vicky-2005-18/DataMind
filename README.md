# 🧠 DataMind — Interactive Machine Learning Discovery & Experimentation Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.64-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.9-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3.49-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-81%20Passed-4CAF50?style=for-the-badge&logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**A fully local, browser-based tabular ML laboratory for safe experimentation, reproducible evaluation, and educational algorithm discovery — no cloud, no API keys, no data leaves your machine.**

[🚀 Quick Start](#-quick-start) · [✨ Features](#-features) · [🏗️ Architecture](#️-architecture) · [📊 What You Can Do](#-what-you-can-do) · [🧪 Testing](#-testing) · [📁 Project Structure](#-project-structure)

</div>

---

## 📖 Overview

DataMind is a **production-quality local ML platform** built with Python, Streamlit, scikit-learn, and SQLite. It guides you through the complete ML lifecycle — from raw CSV upload through model comparison and holdout evaluation — while enforcing strict data science correctness rules at every step.

### Why DataMind?

| Problem | How DataMind Solves It |
|---|---|
| Training data leaks into validation | Preprocessing fitted **inside each CV fold** — zero leakage by design |
| Irreproducible experiments | Every split, fold, seed, and metric recorded in SQLite with SHA-256 fingerprinting |
| Accidental holdout contamination | Holdout finalization is **one-time and irreversible** with exposure tracking |
| Duplicate experiment waste | Submit-token idempotency returns cached results for identical configs |
| Confusing model comparisons | Comparison enforces strict cohort compatibility (same dataset, target, split) |
| "Magic" model numbers | Dummy baseline always included; metrics link to stored records |

---

## ✨ Features

### 🗂️ Dataset Workspace (M1)
- Strict **UTF-8 / UTF-8-BOM CSV parsing** with configurable row, column, and string-length bounds
- **Structural profiling**: row/column counts, duplicates, memory size, cardinality, constant columns, ±∞ guards
- Missingness analysis with role suggestions (target, feature, ignore)
- **Immutable storage**: raw CSV saved under `storage/datasets/<id>/raw.csv` with SHA-256 hash
- Offline demo loaders: Iris, synthetic regression (500 rows), and synthetic 3D blobs (600 rows)

### 🧪 Supervised ML Engine (M2)
- Full **task/target/feature validation** with row-level policies (drop missing target, collapse duplicates, reject conflicting label vectors)
- **Deterministic development/holdout split** with exact row IDs and SHA-256 fingerprint
- **Leakage-free cross-validation**: `ColumnTransformer` fitted inside each fold — verified with spy-transformer test
- Preprocessing: median/mean imputation, standard/minmax/passthrough scaling, one-hot encoding with unknown handling
- **Allowlisted model registry**: Dummy baseline (always included), Logistic Regression, Ridge, Linear Regression, Decision Tree, Random Forest, k-NN
- Champion selection by primary CV metric (macro F1 for classification, RMSE for regression), tie-broken by model complexity order
- Independent metric oracles: macro F1, accuracy, precision, recall, log-loss, ROC-AUC (classification); RMSE, MAE, R² (regression)

### 💾 Persistent MVP (M3)
- Full **trial/experiment history** and failure records in SQLite
- **Workspace lock** (filelock) — single-flight training enforced; no concurrent training collisions
- **Submit-token idempotency** — same config hash returns the cached experiment ID without re-training
- **Recovery service**: on startup marks stale `running` experiments as `interrupted`, detects orphaned artifact directories
- **Holdout finalization**: explicit, one-time, irreversible; `holdout_previously_exposed` flag set on repeat access to same split
- **Comparison service**: strict cohort compatibility (dataset, task, target, split fingerprint, primary metric); raises `INCOMPATIBLE_COMPARISON` for mismatches
- **Prediction service**: schema validation, single-row and batch CSV (up to 500 rows), unseen category handling via OHE, typed `ServiceError` responses

### 📊 Explain & Export (M4)
- **Permutation feature importance** on development rows with non-causal labeling
- **HTML & Markdown report generation** with escaped content, real CV/holdout metrics, failures, and artifact hashes
- **Model ZIP**: fitted pipeline + manifest with checksums (joblib safety warning included)
- **Experiment ZIP**: reports + config + evidence bundle
- **Safe CSV export**: formula injection escaping for spreadsheet safety

### 🔬 Clustering & Discovery (M5)
- **Numeric K-Means lab**: median imputation → standardization → validated `k` bounds
- Inertia, cluster sizes, bounded seeded silhouette sampling (max 2,000 rows), explicit undefined reasons
- **Elbow sweep diagnostics** stored as artifact data (not duplicate trial rows)
- **PCA display projection** clearly separated from full-space clustering and silhouette scoring
- One persisted selected-k trial with model, config, and diagnostic artifacts with checksums
- **Algorithm reference cards**: educational descriptions for all supervised and unsupervised algorithms
- **Interactive playgrounds**: real fitted decision-tree, kNN, and K-Means visualizations with seeded outputs
- Unsupervised/playground results strictly excluded from the supervised comparison leaderboard

### ✅ Final Verification (M6)
- All **81/81 automated tests** passing (T01–T44 required tests represented)
- All **P0/P1 functional requirements** (FR-01–FR-20) implemented and verified
- All **non-functional requirements** (NFR-01–NFR-10) satisfied
- **Performance**: Iris profiling 0.049s (target <3s), Iris experiment 3.917s (target <60s)
- **Ruff linting**: clean for all core application files
- **Fresh environment validated**: offline demos confirmed without network access

---

## 🏗️ Architecture

```
DataMind
│
├── app.py                        # Streamlit entrypoint & router
│
├── datamind/                     # Core application package
│   ├── config.py                 # Validated settings, resource limits, storage paths
│   ├── contracts.py              # Typed DTOs, ServiceError structures, enums
│   │
│   ├── data/                     # Data layer
│   │   ├── ingestion.py          # CSV parser, validation, byte/row/col bounds
│   │   ├── profiling.py          # Structural profiling, cardinality, role suggestions
│   │   └── demos.py              # Offline demo generators (Iris, regression, blobs)
│   │
│   ├── ml/                       # ML layer
│   │   ├── splitting.py          # Deterministic dev/holdout split + CV manifests
│   │   ├── preprocessing.py      # ColumnTransformer pipelines, fold-local fitting
│   │   ├── registry.py           # Allowlisted algorithm registry with param validation
│   │   ├── metrics.py            # Independent metric oracles (classification & regression)
│   │   └── experiment.py         # CV engine, champion selection, development refit
│   │
│   ├── services/                 # Application service layer
│   │   ├── datasets.py           # Dataset CRUD, ingestion orchestration
│   │   ├── experiments.py        # Experiment lifecycle, holdout finalization
│   │   ├── comparison.py         # Cohort-compatible comparison service
│   │   ├── prediction.py         # Schema-validated prediction service
│   │   ├── export.py             # Reports, ZIPs, feature importance
│   │   ├── clustering.py         # K-Means lab orchestration
│   │   ├── playground.py         # Algorithm playground fits
│   │   └── recovery.py           # Startup crash recovery
│   │
│   ├── storage/                  # Persistence layer
│   │   ├── db.py                 # SQLite connection, FK enforcement, migration runner
│   │   ├── migrations/           # SQL migration files (001_initial.sql, ...)
│   │   ├── repositories.py       # Dataset & project repositories
│   │   ├── experiment_repos.py   # Split, experiment, trial, metric, evaluation repos
│   │   ├── artifacts.py          # Atomic file publication, integrity checks
│   │   └── locks.py              # Workspace filelock (single-flight guard)
│   │
│   └── ui/                       # Streamlit UI layer
│       ├── components.py         # Shared UI components, KPI cards, alerts
│       ├── sidebar.py            # Navigation sidebar, project selector
│       └── pages/                # One module per page
│           ├── home.py           # Dashboard & project management
│           ├── datasets.py       # Dataset upload, profiling, role schema
│           ├── explore.py        # Development EDA (distributions, correlation)
│           ├── experiments.py    # CV training, leaderboard, finalize holdout
│           ├── compare.py        # Multi-experiment comparison, bar chart
│           ├── predict.py        # Single-row form + batch CSV upload
│           ├── explain_export.py # Feature importance + report/ZIP exports
│           ├── clustering.py     # K-Means lab, elbow curve, silhouette
│           └── discover.py       # Algorithm cards, interactive playgrounds
│
├── scripts/                      # Setup, run, and verification scripts
│   ├── setup.ps1                 # Automated setup (PowerShell)
│   ├── run.ps1                   # Launch the app (PowerShell)
│   ├── run.bat                   # Launch the app (Batch)
│   ├── verify_environment.py     # Dependency & storage health check
│   ├── smoke_demo.py             # M0/M1 service-layer smoke test
│   └── final_verification.py    # M6 evidence measurement (timing + memory)
│
├── examples/                     # Example ML workflows
│   ├── demo_m2.py                # Supervised ML end-to-end demo (Iris + regression)
│   ├── demo_m3_mvp.py            # M3 persistence, recovery, prediction demo
│   ├── demo_m4_export.py         # M4 export, importance, report demo
│   └── demo_m5.py                # M5 clustering & playground demo
│
├── tests/                        # Automated test suite (81 tests)
│   ├── unit/                     # Unit tests per module
│   ├── integration/              # Integration tests (DB, service layers)
│   └── ui/                       # Streamlit AppTest smoke tests
│
└── docs/                         # Specifications
    ├── ML_SPEC.md                # ML correctness rules, metric definitions
    ├── DATA_CONTRACTS.md         # CSV bounds, missingness rules, role logic
    ├── TEST_PLAN.md              # T01–T44 test plan
    └── SERVICE_CONTRACTS.md      # Service-layer API contracts
```

**Design Principle**: UI → Services → ML/Data → Storage. No layer skips another. Preprocessing always fitted within CV folds; the saved champion is refit on development rows only.

---

## 📊 What You Can Do

| Page | What It Does |
|---|---|
| **Home** | Create & switch projects; persist across browser restarts |
| **Datasets** | Upload CSV or load an offline demo; inspect profiling report |
| **Explore** | Development-set EDA: distributions, class balance, correlation heatmap |
| **Experiments** | Configure & run CV training; view per-fold metrics; finalize holdout |
| **Compare** | Select compatible experiments; ranked leaderboard + bar chart |
| **Predict** | Type single-row values or upload a batch CSV; download results |
| **Explain & Export** | Feature importance; download HTML/Markdown report, Model ZIP, Experiment ZIP |
| **Clustering** | Run K-Means lab; elbow curve; silhouette; PCA scatter |
| **Discover** | Algorithm reference cards; interactive decision-tree, kNN, K-Means playgrounds |

---

## 🚀 Quick Start

> **Requires**: Windows 11, Python 3.12.x (64-bit)

### Option A — Automated Setup (Recommended)

```powershell
# 1. Clone the repository
git clone https://github.com/vicky-2005-18/DataMind.git
cd DataMind

# 2. Run the automated setup (creates venv, installs deps, creates .env, cleans storage)
.\scripts\setup.ps1

# 3. Launch the app
.\scripts\run.ps1
```

Then open **http://127.0.0.1:8501** in your browser.

### Option B — Manual Setup

```powershell
# Create virtual environment
py -3.12 -m venv .venv

# Install locked dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt

# Install package in editable mode
.\.venv\Scripts\python.exe -m pip install -e . --no-deps

# Create .env (required — gitignored for security)
Copy-Item .env.example .env

# Verify environment
.\.venv\Scripts\python.exe scripts\verify_environment.py

# Launch
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

---

## 🧪 Testing

```powershell
# Run the full test suite (81 tests)
.\.venv\Scripts\python.exe -m pytest -q

# Run with verbose output
.\.venv\Scripts\python.exe -m pytest -v

# Lint with Ruff
.\.venv\Scripts\python.exe -m ruff check .

# Run offline M5 clustering demo
.\.venv\Scripts\python.exe examples\demo_m5.py

# Run final performance evidence measurement
.\.venv\Scripts\python.exe scripts\final_verification.py
```

### Test Coverage Summary

| Test Group | Tests | Status |
|---|---|---|
| T01 — DB migration idempotency | 1 | ✅ |
| T02–T07 — CSV validation & offline demos | 6 | ✅ |
| T08–T19 — Supervised ML correctness | 12 | ✅ |
| T20–T31, T41–T42 — Persistence & recovery | 14 | ✅ |
| T32–T34 — Explain & export | 3 | ✅ |
| T35–T38 — Clustering & playground | 4 | ✅ |
| T39 — Dataset change invalidation | 1 | ✅ |
| T40 — Fresh environment walkthrough | 1 | ✅ |
| UI smoke tests | 5 | ✅ |
| **Total** | **81** | **✅ All passing** |

---

## 📈 Verified Performance

Measured on **Windows 11, Python 3.12.10, AMD64 (12 logical CPUs)**:

| Benchmark | Result | Target |
|---|---|---|
| Iris import + profiling | **0.049 s** | < 3 s |
| Iris 3-model CV experiment | **3.917 s** | < 60 s |
| Peak memory (profiling) | 0.512 MiB | — |
| Peak memory (experiment) | 0.841 MiB | — |

**Champion result** (Iris classification, 5-fold stratified CV):
- Model: Logistic Regression
- CV macro-F1: **0.9580 ± 0.0268** (dummy baseline: 0.1667)
- Holdout macro-F1: **0.9333**

---

## 🔒 ML Correctness Guarantees

DataMind enforces these data science rules automatically:

- ✅ **Target exclusion**: target column never appears in feature matrix
- ✅ **Leakage-free preprocessing**: imputers and scalers fitted only on CV training fold rows
- ✅ **Spy-transformer verification**: automated test confirms test/validation row IDs never enter `fit` or `fit_transform`
- ✅ **Identical folds**: all competing models evaluated on the exact same fold splits
- ✅ **Holdout sequestration**: holdout metrics unavailable until explicit, one-time finalization
- ✅ **Dummy baseline**: always included; result disclosed when baseline wins
- ✅ **N/A with reason**: metrics reported as N/A with explanation when undefined (e.g., single-class fold)
- ✅ **Deterministic seeds**: every random seed recorded; identical config reproducible
- ✅ **Artifact integrity**: SHA-256 checksums stored for all persisted artifacts

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and adjust as needed:

```env
# Storage root (default: ./storage)
DATAMIND_STORAGE_ROOT=./storage

# Max CSV upload size in bytes (default: 50 MB)
DATAMIND_MAX_CSV_BYTES=52428800

# Max rows per dataset (default: 100,000)
DATAMIND_MAX_ROWS=100000
```

---

## 📦 Key Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | 1.64.0 | Browser UI framework |
| `pandas` | 3.0.6 | Tabular data operations |
| `numpy` | 2.5.3 | Numerical computing |
| `scikit-learn` | 1.9.1 | ML algorithms & preprocessing |
| `plotly` | 7.1.0 | Interactive charts |
| `pydantic` | 2.13.5 | Config & contract validation |
| `joblib` | — | Pipeline serialization |
| `filelock` | — | Workspace concurrency lock |
| `jinja2` | — | HTML report templating |
| `python-dotenv` | — | Environment config loading |

---

## 🗺️ Milestone Roadmap

| Milestone | Description | Status |
|---|---|---|
| **M0** | Foundation: package structure, SQLite migrations, workspace lock, Streamlit entrypoint | ✅ Complete |
| **M1** | Dataset workspace: CSV validation, immutable storage, offline demos, structural profiling | ✅ Complete |
| **M2** | Supervised ML engine: splits, leakage-free CV, champion selection, persistence | ✅ Complete |
| **M3** | Persistent MVP: trial history, idempotency, recovery, holdout finalization, prediction | ✅ Complete |
| **M4** | Explain & Export: permutation importance, HTML/MD reports, model/experiment ZIPs | ✅ Complete |
| **M5** | Clustering & Discovery: K-Means lab, elbow, silhouette, algorithm cards, playgrounds | ✅ Complete |
| **M6** | Final verification: full audit, performance evidence, fresh-env validation, lint clean | ✅ Complete |

---

## ⚠️ Known Limitations

- Local single-user operation only (no authentication, no multi-user support)
- Bounded tabular CSV only — no time-series, image, or text data
- Synchronous CPU training — large datasets may be slow
- No grouped or time-series cross-validation
- Limited allowlisted algorithm registry (no XGBoost, neural nets, etc.)
- Permutation importance is non-causal (correlation-based ordering only)
- PCA is for 2D display only, not dimensionality reduction for modeling
- Synthetic playground results are educational demonstrations, not experiment trials
- An exposed holdout is not restored to untouched status by changing seeds
- `tracemalloc` measures Python heap allocation, not whole-process RSS

---

## 📚 Documentation

| Document | Purpose |
|---|---|
| [`START_HERE.md`](START_HERE.md) | Project explanation, file index, architecture background |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Layer design, data flow, module responsibilities |
| [`docs/internal/PRD.md`](docs/internal/PRD.md) | Product requirements, acceptance criteria (FR-01–FR-20, NFR-01–NFR-10) |
| [`docs/ML_SPEC.md`](docs/ML_SPEC.md) | ML correctness rules, metric definitions, leakage-prevention contract |
| [`docs/DATA_CONTRACTS.md`](docs/DATA_CONTRACTS.md) | CSV parsing bounds, missingness rules, role logic |
| [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md) | Full test plan (T01–T44) |
| [`docs/SERVICE_CONTRACTS.md`](docs/SERVICE_CONTRACTS.md) | Service-layer API contracts and error codes |
| [`PROJECT_STATE.md`](PROJECT_STATE.md) | Session-by-session implementation evidence and handover notes |

---

## 🤝 Contributing

This project follows the engineering rules in [`AGENTS.md`](AGENTS.md). Key principles:

1. **No leakage** — preprocessing always inside CV folds
2. **No placeholders** — unimplemented pages must say so
3. **Verified evidence** — never claim tests passed without running them
4. **Honest reporting** — all metrics link to stored SQLite records

---

## 📄 License

MIT License

---

<div align="center">

Built with ❤️ using Python, Streamlit, scikit-learn, and SQLite.

**All computation runs locally. Your data never leaves your machine.**

</div>
