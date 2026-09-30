# Windows setup and runbook

## Before code is generated

1. Extract the ZIP and open its inner folder in Antigravity.
2. Keep all relative paths together. You can rename the outer project directory.
3. Paste ANTIGRAVITY_START_PROMPT.md into agent chat.
4. The agent first creates application code, `pyproject.toml` and tested dependency lockfiles.

**Do not run `streamlit run app.py` before M0 creates app.py. This pack contains specifications, not the finished app.**

## Python environment

Use Python 3.11 as the initial development target. Let the agent verify compatibility with the resolved dependencies and record any justified version adjustment; this is not a claim that 3.11 is the newest Python.

From the project folder in PowerShell:

```powershell
py -3.11 --version
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

Direct virtualenv Python commands avoid PowerShell activation-policy changes. If `py -3.11` cannot find Python, install the chosen Python version or select an already installed supported one and document that decision.

## Dependency selection for M0

Runtime direct dependencies: streamlit, pandas, numpy, scikit-learn, plotly, joblib, pydantic, filelock, python-dotenv and jinja2. SQLite uses Python's standard `sqlite3` module; do not pip-install a package named sqlite3. Testing/tooling: pytest and ruff; Streamlit supplies its app testing utilities in supported versions.

Agent should declare compatible ranges in pyproject, install in the clean environment, verify imports and smoke behavior, then capture the exact resolved runtime and development dependency sets. Lockfiles must be generated from a tested environment, not guessed from current marketing versions. Use one dependency-management strategy consistently.

## After M0 has generated and verified the files

For a clean checkout with the generated lockfiles:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Use the local URL printed by Streamlit. To stop, press Ctrl+C in that terminal. Existing storage stays on disk.

Only copy `.env.example` on the first setup; do not overwrite an existing `.env` containing deliberate local changes. No API key is required for this application's core runtime. Antigravity's own access/model settings are separate from DataMind's runtime dependencies.

## Verify the implementation

After the agent creates the corresponding tests/scripts:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe scripts\verify_environment.py
.\.venv\Scripts\python.exe scripts\smoke_demo.py
```

Do not report these commands as passed until they have actually run. Use direct interpreter paths consistently so global package installations do not mask missing dependencies.

## Troubleshooting

| Symptom | Check / action |
|---|---|
| Missing Python version | Check installed interpreters; install/select the documented target |
| ModuleNotFoundError | Run pip through the same `.venv` interpreter used to launch app |
| Port busy | Close previous app or use `--server.port 8502` |
| SQLite locked | End active operation normally; inspect lock ownership; do not delete DB |
| Stale running experiment | Run implemented guarded recovery; preserve old record as interrupted |
| Model version mismatch | Use recorded compatible environment or retrain as a new experiment |
| Rerun unexpectedly retrains | Fix submit-token/service logic; do not hide duplicate history |

## Delivery runbook

Record actual environment and tested commands in the implementation README. Do not commit `.venv`, `.env`, uploaded datasets, SQLite files or trained models. Commit specs, code, small synthetic fixtures, migration files and lockfiles. Docker is optional after the local demo works; it is not a prerequisite.

## Quick Start (Automated Setup)

### Option 1: Run Setup Script (Recommended for First Time)

1. Open PowerShell in the DataMind project directory
2. Run the setup script:
   ```powershell
   .\scripts\setup.ps1
   ```
3. After setup completes, run:
   ```powershell
   .\scripts\run.ps1
   ```

### Option 2: Direct Startup (If Dependencies Already Installed)

```powershell
.\scripts\run.ps1
```

### Option 3: Manual Startup

```powershell
streamlit run app.py
```

## Available Scripts

### `scripts/setup.ps1`
- **Purpose**: Install all required dependencies and configure environment
- **When to use**: First time setup or if you encounter dependency issues
- **What it does**:
  - Checks Python installation
  - Upgrades pip
  - Installs all project dependencies
  - **Automatically creates .env file from .env.example** (fixes missing file issue on fresh clones)
  - **Cleans up any existing storage directory** (removes stale data from ZIP downloads)

### `scripts/run.ps1`
- **Purpose**: Start DataMind with full checks
- **When to use**: Regular startup
- **What it does**:
  - Checks Python installation
  - Verifies correct directory
  - Installs/updates dependencies if needed
  - **Cleans up any existing storage directory** (removes stale data from ZIP downloads)
  - **Automatically creates .env file if missing**
  - Starts the application

### `scripts/run.bat`
- **Purpose**: Start DataMind with full checks (Batch version)
- **When to use**: Regular startup on Windows without PowerShell
- **What it does**: Same as `scripts/run.ps1` but for Command Prompt

## Troubleshooting

### "streamlit is not recognized"
**Solution**: Run the setup script first:
```powershell
.\scripts\setup.ps1
```

### "python is not recognized"
**Solution**: Install Python 3.11+ from https://www.python.org/
- **Important**: Check "Add Python to PATH" during installation

### Script execution policy error
**Solution**: Allow script execution in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Dependencies not installing
**Solution**: Try upgrading pip first:
```powershell
python -m pip install --upgrade pip
pip install -e .
```

## System Requirements

- **Python**: 3.11 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Disk Space**: 500MB for dependencies

## After Startup

Once DataMind starts:
1. The application will open in your default browser
2. Navigate to `http://localhost:8501` if it doesn't open automatically
3. Create a project or load a demo dataset to get started

## Stopping the Application

Press `Ctrl+C` in the PowerShell window to stop the DataMind server.
