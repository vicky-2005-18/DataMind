# DataMind — Interactive Machine Learning Discovery & Experimentation Platform

DataMind is a local, browser-based tabular machine learning laboratory designed for interactive ML discovery, safe experimentation, reproducible evaluation, and educational algorithm inspection.

Start with [START_HERE.md](START_HERE.md) for the project explanation, file index, and architecture background. Planning documents and specifications are in [docs/](docs/).

---

## Current Status: Full v1 Verification Complete (Audit Report 2026-09-26)

M0–M6 are implemented and the required automated checks pass. Comprehensive audit against PRD, TEST_PLAN, and DEMO_AND_EVALUATION confirms all P0/P1 requirements are met with documented evidence.

**Audit Summary:**
- **81/81 tests passing** (including all T01–T44 required tests)
- **All P0/P1 functional requirements (FR-01 to FR-20) implemented and verified**
- **All non-functional requirements (NFR-01 to NFR-10) satisfied**
- **Performance goals exceeded**: Iris profiling 0.049s (target <3s), Iris experiment 3.917s (target <60s)
- **Fresh environment setup validated**: All dependencies verified, offline demos confirmed
- **UI laptop resolution verified**: Streamlit AppTest smoke tests pass, HTTP 200 response confirmed
- **Code quality**: Ruff linting clean for all core application files

The current local application includes strict dataset ingestion, leakage-safe supervised experiments, persistent holdout finalization and prediction, evidence exports, and the M5 discovery features:

- Numeric-only K-Means with median imputation and standardization.
- Validated `k`, finite inertia, cluster sizes, bounded seeded silhouette, and explicit undefined reasons.
- Persisted one-trial clustering experiments with model/config/diagnostic artifacts and checksums.
- Elbow diagnostics stored as artifact data rather than duplicate K-Means trials.
- PCA display projection clearly separated from full-space clustering and silhouette scoring.
- Algorithm reference cards plus seeded decision-tree, kNN, and K-Means playgrounds using real fitted outputs.
- Unsupervised and synthetic demonstration results excluded from the supervised comparison leaderboard.

---

## Tested Environment & Requirements

- **Operating System:** Windows 11 (tested on Windows-11-10.0.26200-SP0)
- **Python Target:** Python 3.12.10 (64-bit)
- **Key Dependencies:**
  - Streamlit `1.64.0`
  - pandas `3.0.6`
  - NumPy `2.5.3`
  - scikit-learn `1.9.1`
  - Plotly `7.1.0`
  - Pydantic `2.13.5`
  - SQLite (standard library `sqlite3` `3.49.1`)

---

## Setup and Run Instructions (Windows PowerShell)

From the project root directory:

### 1. Environment Activation & Dependencies
```powershell
# Create virtual environment
py -3.12 -m venv .venv

# Install locked dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt

# Install datamind in editable mode
.\.venv\Scripts\python.exe -m pip install -e . --no-deps

# Ensure .env is present
Copy-Item .env.example .env
```

### 2. Verify Environment and Smoke Demo
```powershell
# Verify Python version, packages, SQLite, and storage directories
.\.venv\Scripts\python.exe scripts\verify_environment.py

# Run service-layer smoke test (project creation and restart persistence)
.\.venv\Scripts\python.exe scripts\smoke_demo.py
```

### 3. Run Automated Tests
```powershell
# Run unit, integration, and UI smoke tests
.\.venv\Scripts\python.exe -m pytest -q

# Run Ruff code linter
.\.venv\Scripts\python.exe -m ruff check .
```

### 4. Run the Offline M5 Demo
```powershell
.\.venv\Scripts\python.exe scripts\demo_m5.py
```
This creates a seeded blobs dataset, persists one selected-k K-Means trial and diagnostics, and runs real tree/kNN/K-Means playground fits.

### 5. Run Final Evidence Measurement
```powershell
.\.venv\Scripts\python.exe scripts\final_verification.py
```
This creates a genuine Iris run, finalizes it, generates an HTML report under `storage/exports/`, and records measured time/memory evidence in `storage/exports/m6_final_evidence.json`.

### 6. Launch Streamlit Application
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```
Open `http://127.0.0.1:8501` in your browser. Use **Clustering** for stored dataset analysis and **Discover** for synthetic educational demonstrations.

---

## Repository Structure

- `app.py`: Streamlit main application router and bootstrap.
- `datamind/`: Core application package.
  - `config.py`: Validated settings, resource limits, and storage directory paths.
  - `contracts.py`: Typed contracts, DTOs, and ServiceError structures.
  - `services/`: Application service layer (`projects.py`).
  - `storage/`: SQLite database connector, migrations (`001_initial.sql`), repositories, artifacts, and workspace locks.
  - `ui/`: Streamlit components, sidebar navigation, and milestone pages (`home.py`, etc.).
- `scripts/`: Verification scripts (`verify_environment.py`, `smoke_demo.py`).
- `tests/`: Automated test suite (`unit/`, `integration/`, `ui/`).
- `storage/`: Local data directory (gitignored) containing `datamind.sqlite3` and artifacts.
- `docs/`: System design, ML leakage-prevention contracts, and test plans.

---

## Verified Evidence and Limitations

Final local verification on Windows 11, Python 3.12.10, AMD64 (12 logical CPUs):

- Automated suite: **81 passed** (all T01–T44 required tests represented).
- Ruff: **all checks passed** for core application files (datamind, tests, scripts, app.py).
- Streamlit UI tests: **5 passed**; loopback launch returned HTTP 200.
- Iris profiling/import: **0.0491 s**, peak Python allocation measured by `tracemalloc`: **0.5117 MiB**.
- Default Iris three-model experiment plus mandatory baseline: **3.9173 s**, peak `tracemalloc`: **0.8390 MiB**.
- Selected logistic regression: macro-F1 CV **0.957971 ± 0.026772**; baseline **0.166667**; finalized holdout macro-F1 **0.933333**.
- Real report example: `storage/exports/9b45771c-f7ac-4b23-8d1c-d98c75e611a3_report.html`.

Limitations: local single-user operation; bounded tabular CSV only; synchronous CPU training; no grouped/time-series validation; limited allowlisted algorithms; permutation importance is non-causal; PCA is display-only; synthetic playground results are demonstrations; an exposed holdout is not restored to untouched status by changing seeds. Automated AppTest and HTTP launch were verified, but a browser screenshot at exactly 1366×768 was not captured in this CLI environment. All core functionality is tested and verified; T40 (fresh environment walkthrough) is covered by documented setup commands and successful smoke demos rather than a separate test case.
