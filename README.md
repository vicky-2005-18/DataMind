# DataMind — Interactive Machine Learning Discovery & Experimentation Platform

DataMind is a local, browser-based tabular machine learning laboratory designed for interactive ML discovery, safe experimentation, reproducible evaluation, and educational algorithm inspection.

Start with [START_HERE.md](START_HERE.md) for the project explanation, file index, and architecture background. Planning documents and specifications are in [docs/](docs/).

---

## Current Status: Milestone 0 (Foundation) Complete

**M0 — Foundation** has been implemented and verified:
- Modular Python package `datamind` installed in editable mode.
- SQLite migration runner executing the baseline schema (`datamind/storage/migrations/001_initial.sql`).
- Persistent project management service and repository with UUID generation and timestamp tracking.
- Streamlit application shell (`app.py`) with explicit sidebar navigation and honest empty states for future milestone pages.
- Automated test suite covering settings, migration idempotency, project persistence, and AppTest UI smoke launch.
- Verified dependency lockfiles (`requirements.lock.txt`, `requirements-dev.lock.txt`).

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

### 4. Launch Streamlit Application
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```
Open `http://127.0.0.1:8501` in your browser.

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
