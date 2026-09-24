# Project state and handover

Last updated: 2026-09-24
Current stage: M6 — Final verification complete with two documented manual-evidence limitations.

## Authoritative status

- M0 Foundation, M1 Dataset Workspace, M2 Supervised ML Engine, and M3 Persistent MVP implemented and verified on local Windows 11 environment.
- Strict CSV/UTF-8/UTF-8-BOM parsing, byte limits, row/column/string bounds, and missingness rules enforced.
- Immutable dataset files stored under `storage/datasets/<id>/raw.csv` with recorded SHA-256 and parser metadata.
- Offline demo generators (Iris, synthetic regression, 3D blobs) verified without network.
- Structural dataset profiling: row/column counts, duplicates, memory size, cardinality, constant checks, ±infinity guards, and role suggestions.
- Modeling protocol: task/target confirmation, feature selection, row policies (drop missing target, collapse duplicate rows, reject conflicting target feature vectors).
- Split engine: exact deterministic development/holdout split and StratifiedKFold/KFold CV manifests with source row IDs and SHA-256 fingerprinting.
- Preprocessing pipelines: ColumnTransformer with median/mean imputer, standard/minmax/passthrough scaler, OneHotEncoder (with unknown ignore and column cap), fitted fold-locally inside each CV fold to strictly prevent leakage.
- Spy-transformer leakage verification: verified that test/validation row IDs never enter transformer fit or fit_transform calls.
- Model registry: allowlisted algorithms with parameter validation (dummy classifier/regressor baselines, logistic regression, linear regression, ridge, decision tree, random forest, kNN).
- Cross-validation: identical CV folds across all competing models, per-fold metric recording, population standard deviation (ddof=0).
- Champion selection: primary CV metric only (macro F1 for classification, RMSE for regression), tie-broken by model complexity order. Refit on development set only; holdout metrics sequestered and unavailable.
- SQLite persistence: splits, experiments, trials, metrics, and evaluations saved atomically with foreign keys. Full trial history and evaluation records survive server restarts.
- Workspace lock (filelock) enforces single-flight training/finalization operations. Submit token idempotency prevents duplicate experiments on identical configs.
- Holdout finalization: explicit, one-time, irreversible action; first evaluation records `holdout_previously_exposed=False`; subsequent evaluations on the same split set `holdout_previously_exposed=True`.
- Comparison service: enforces strict cohort compatibility (same dataset, task, target, split fingerprint, primary metric). Incompatible pairs raise `INCOMPATIBLE_COMPARISON`.
- Prediction: validates raw feature schema against `input_schema.json`, reuses the saved fitted pipeline (`champion.joblib`), supports single-row and bounded CSV batches (max 500 rows). Unseen categories handled via OHE `handle_unknown='ignore'`. Missing model raises `MODEL_UNAVAILABLE`.
- Recovery service: on startup detects stale `running` experiments and marks them `interrupted`; detects orphaned experiment directories and tags them with `.orphan` marker.
- Streamlit UI: Explore page (development EDA), Experiments page (CV training, leaderboard, finalize holdout, experiment history), Compare page (compatible comparison leaderboard + bar chart), Predict page (single-row input form + CSV batch upload with results table and download).
- M5 K-Means lab persists exactly one selected-k trial with model, configuration and diagnostic artifacts; elbow points remain diagnostic data rather than trial rows.
- M5 preprocessing uses median imputation and standardization; k is bounded by row and distinct transformed-row counts.
- Inertia, cluster sizes, seeded silhouette sampling (maximum 2,000 rows), explicit undefined reasons, and PCA display coordinates are recorded.
- Algorithm cards and seeded decision-tree, kNN and K-Means playgrounds render actual fitted outputs; playground results remain synthetic demonstrations.
- Supervised comparison rejects clustering experiments and the UI filters them from its leaderboard.
- Targeted M5 evidence: 4/4 T35–T38 tests passing; 4/4 UI smoke tests passing; changed-file Ruff checks passing; `scripts/demo_m5.py` completed offline.
- Next action: M6 final audit, including unresolved M4 audit findings and full-project lint cleanup.

## Decisions in force

Python + Streamlit + scikit-learn + SQLite; local single user; tabular CSV; CPU; no paid API dependency. MVP covers supervised tasks. Full v1 includes discovery and K-Means. Detailed limits and evaluation rules are in docs/ML_SPEC.md and docs/DATA_CONTRACTS.md.

## Update this after each implementation session

| Field | Record actual evidence |
|---|---|
| Date and milestone | 2026-09-21 • M0 — Foundation |
| Implemented behavior | Virtualenv created, dependencies resolved and locked, `datamind` package created, SQLite migration runner (`001_initial.sql`), project repository & service, atomic artifact utilities, workspace lock, Streamlit entrypoint (`app.py`), sidebar navigation and honest empty states for future milestone pages. |
| Changed paths | `app.py`, `pyproject.toml`, `requirements.lock.txt`, `requirements-dev.lock.txt`, `.streamlit/config.toml`, `.env`, `datamind/*`, `tests/*`, `scripts/*`, `README.md`, `TASKS.md`, `PROJECT_STATE.md` |
| Commands run | `py -3.12 -m venv .venv`<br>`pip install streamlit pandas numpy scikit-learn plotly joblib pydantic filelock python-dotenv jinja2 pytest ruff`<br>`pip install -e . --no-deps`<br>`pytest -q`<br>`ruff check .`<br>`python scripts/verify_environment.py`<br>`python scripts/smoke_demo.py` |
| Test result | 9 passed in 1.40s (`pytest -q`), 0 lint errors (`ruff check .`), all environment and smoke checks passed. |
| Manual check | Streamlit AppTest verified home page title and radio controls. Database initialized with tables and foreign keys enabled. Projects persist across process restarts. |
| Known defects | None. |
| Environment | Python 3.12.10, Streamlit 1.64.0, pandas 3.0.6, scikit-learn 1.9.1, NumPy 2.5.3, Plotly 7.1.0, SQLite 3.49.1, Windows 11 (Windows-11-10.0.26200-SP0). |
| Decision changes | Selected installed Python 3.12.10 instead of 3.11 as permitted by `docs/SETUP_WINDOWS.md`. |
| Next smallest task | M1 — Dataset workspace: CSV validation, immutable storage, offline demos, structural profiling. |

| Field | Record actual evidence |
|---|---|
| Date and milestone | 2026-09-21 • M1 — Dataset workspace |
| Implemented behavior | Strict UTF-8/UTF-8-BOM CSV parser with row/column/string bounds; missingness and infinity validation; offline Iris, synthetic regression, and 3D blobs demo loaders; structural profiling (duplicates, counts, cardinality, nulls, constant columns); SQLite dataset repository; immutable raw CSV artifact store with SHA-256; Streamlit Datasets UI page with upload, demo loading, KPI cards, quality warnings, role schema, and raw table preview. |
| Changed paths | `datamind/contracts.py`, `datamind/data/*` (`ingestion.py`, `profiling.py`, `demos.py`), `datamind/storage/repositories.py`, `datamind/services/datasets.py`, `datamind/ui/pages/datasets.py`, `scripts/smoke_demo.py`, `tests/unit/*` (`test_ingestion.py`, `test_demos.py`, `test_profiling.py`), `tests/integration/test_datasets.py`, `tests/ui/test_app_smoke.py`, `TASKS.md`, `PROJECT_STATE.md` |
| Commands run | `pytest -q`<br>`ruff check .`<br>`python scripts/verify_environment.py`<br>`python scripts/smoke_demo.py` |
| Test result | 26 passed in 3.27s (`pytest -q`), 0 lint errors (`ruff check .`), all environment and smoke checks passed. Tests T02–T07 passed. |
| Manual check | Verified Datasets UI tabs: loaded Iris demo, synthetic regression, and synthetic blobs. Checked KPI metric display, duplicate warning alert, feature role table, and raw table preview. Verified immutable file writes in `storage/datasets/<id>/raw.csv`. |
| Known defects | None. |
| Environment | Python 3.12.10, Streamlit 1.64.0, pandas 3.0.6, scikit-learn 1.9.1, NumPy 2.5.3, Plotly 7.1.0, SQLite 3.49.1, Windows 11. |
| Decision changes | None. |
| Next smallest task | M2a — Modeling protocol: target confirmation, feature roles, row policies, exact split manifests, and development-only EDA. |

| Field | Record actual evidence |
|---|---|
| Date and milestone | 2026-09-21 • M2 — Correct Supervised ML Engine |
| Implemented behavior | Task/target/feature validation; row policies (missing target drop, exact duplicate collapse, conflicting label rejection); deterministic split manifests with exact row IDs and SHA-256 fingerprint deduplication; development-only EDA (distributions, class balance, correlation heatmap); unfitted preprocessing pipelines (SimpleImputer, StandardScaler/MinMaxScaler, OneHotEncoder with column cap); allowlisted algorithm registry with parameter validation (dummy, logistic regression, linear regression, ridge, decision trees, random forests, kNN); leakage-free CV engine fitting transformers inside folds; independent metric oracles (macro F1, accuracy, precision, recall, log loss, ROC-AUC, RMSE, MAE, R²); champion selection by primary CV metric and tie-breaking by complexity order; development refit and pipeline bundle persistence; holdout metrics sequestered; SQLite split and experiment repositories; Streamlit Explore and Experiments UI pages. |
| Changed paths | `datamind/contracts.py`, `datamind/ml/*` (`modeling.py`, `splitting.py`, `preprocessing.py`, `registry.py`, `metrics.py`, `experiment.py`), `datamind/storage/experiment_repos.py`, `datamind/services/experiments.py`, `datamind/ui/pages/explore.py`, `datamind/ui/pages/experiments.py`, `scripts/demo_m2.py`, `tests/unit/test_m2_modeling.py`, `tests/ui/test_app_smoke.py`, `TASKS.md`, `PROJECT_STATE.md` |
| Commands run | `pytest -q`<br>`ruff check .`<br>`python scripts/verify_environment.py`<br>`python scripts/smoke_demo.py`<br>`python scripts/demo_m2.py` |
| Test result | 47 passed in 4.18s (`pytest -q`), 0 lint errors (`ruff check .`), all environment and smoke checks passed. Tests T08–T19, T43, T44 passed including spy-transformer leakage test. |
| Manual check | Executed `scripts/demo_m2.py`: Iris 5-fold CV (champion: `logistic_regression`, macro F1: 0.9580, baseline: 0.1667) and Synthetic Regression 5-fold CV (champion: `linear_regression`, RMSE: 15.3017, baseline: 108.2645). Verified holdout sequestration, database persistence, and Explore/Experiments Streamlit UI rendering. |
| Known defects | None. |
| Environment | Python 3.12.10, Streamlit 1.64.0, pandas 3.0.6, scikit-learn 1.9.1, NumPy 2.5.3, Plotly 7.1.0, SQLite 3.49.1, Windows 11. |
| Decision changes | None. |
| Next smallest task | M3 — Persistent MVP: trial/experiment history, workspace lock, submit idempotency, holdout finalization, model prediction. |

| Field | Record actual evidence |
|---|---|
| Date and milestone | 2026-09-21 • M3 — Persistent MVP |
| Implemented behavior | Complete trial/experiment history and failure records in SQLite; `WorkspaceLock` (filelock) enforcing single-flight training/finalization; submit token idempotency (same config hash returns cached experiment without re-training); guarded `RecoveryService` that marks stale `running` experiments as `interrupted` and detects orphaned experiment directories with `.orphan` markers; explicit idempotent holdout finalization via `ExperimentService.finalize_experiment()` (first call scores champion against sequestered holdout; subsequent calls return same immutable `HoldoutEvaluation`); `holdout_previously_exposed` flag set `True` on any finalizations sharing the same split; `ComparisonService` enforcing strict cohort compatibility (dataset, task, target, split fingerprint, primary metric) with `INCOMPATIBLE_COMPARISON` error for mismatches; `PredictionService` validating raw feature schema against `input_schema.json`, reusing saved fitted `champion.joblib`, supporting single-row and bounded CSV batches (max 500 rows), handling unseen categories and extra columns, raising typed `ServiceError` for schema mismatches and missing/corrupt artifacts; Streamlit Experiments page with finalize holdout section, idempotency display, previously-exposed warning, holdout metrics table, confusion matrix, and full experiment history grid; Compare page with multiselect + ComparisonService integration, ranked leaderboard, bar chart, and config diff table; Predict page with single-row typed input form and batch CSV upload with BOM handling, results table with class probabilities, and CSV download. |
| Changed paths | `datamind/config.py` (added `locks_dir`, `storage_root`), `datamind/services/recovery.py` (fixed import, connection pattern), `datamind/ui/pages/experiments.py` (M3 finalize holdout + history), `datamind/ui/pages/compare.py` (ComparisonService integration), `datamind/ui/pages/predict.py` (PredictionService UI), `scripts/demo_m3_mvp.py` (new), `tests/unit/test_m3_mvp.py` (new, 18 tests T20-T31 T41 T42), `TASKS.md`, `PROJECT_STATE.md` |
| Commands run | `pytest -q`<br>`pytest tests/unit/test_m3_mvp.py -v`<br>`ruff check .`<br>`python scripts/demo_m3_mvp.py` |
| Test result | **65 passed in 7.37s** (`pytest -q`), 0 lint errors (`ruff check .`). All 18 M3 tests (T20–T31, T41, T42) pass including: single trial failure preserved, all-candidates-fail experiment, submit token idempotency, recovery skip-when-locked, stale experiment marking, persistence restart, idempotent finalization, holdout previously-exposed flag, incompatible comparison rejection, model reload consistency, schema validation (reorder/missing/extra/invalid), unseen category handling, missing/corrupt artifact errors, cross-project rejection, orphaned artifact quarantine, row limit enforcement, empty input rejection. |
| Manual check | Executed `scripts/demo_m3_mvp.py` (with `PYTHONIOENCODING=utf-8`): created project `M3 Demo 8b84c9`; ran Iris CV experiment 1 (Logistic + RandomForest, champion macro F1 CV=0.9580); confirmed idempotent second submit returns same experiment ID; reloaded experiment from fresh SQLite repo; reconcile returned `{interrupted: 0, trials: 0, orphans: 0}`; holdout finalized (f1_macro=0.9333, accuracy=0.9333); second finalize returned same evaluation ID; ran experiment 2 (KNN) on same split; finalized → `holdout_previously_exposed=True`; single-row prediction: sepal_length=5.1 → species=setosa (P=0.9808); model reload consistency verified; missing columns correctly rejected with PREDICTION_SCHEMA_MISMATCH; batch 10-row prediction returned 5×setosa; compatible comparison succeeded; incompatible cross-task comparison rejected with INCOMPATIBLE_COMPARISON. |
| Known defects | None. |
| Environment | Python 3.12.10, Streamlit 1.64.0, pandas 3.0.6, scikit-learn 1.9.1, NumPy 2.5.3, Plotly 7.1.0, SQLite 3.49.1, Windows 11. |
| Decision changes | None. |
| Next smallest task | M4 — Explain and Export: bounded permutation feature importance, HTML/Markdown experiment report, ZIP bundle with manifest and checksums. |

| Field | Record actual evidence |
|---|---|
| Date and milestone | 2026-09-24 • M5 — Clustering and interactive discovery |
| Implemented behavior | Numeric K-Means lab with median imputation, standardization, validated k, inertia, cluster sizes, bounded seeded silhouette and N/A reasons, elbow sweep diagnostics, PCA display projection, one persisted selected-k trial, registered artifact hashes, reviewed algorithm cards, and real seeded tree/kNN/K-Means playground outputs. Clustering and playground results remain outside the supervised leaderboard. |
| Changed paths | `datamind/contracts.py`, `datamind/services/clustering.py`, `datamind/services/playground.py`, `datamind/services/comparison.py`, `datamind/ui/pages/clustering.py`, `datamind/ui/pages/discover.py`, `datamind/ui/pages/compare.py`, `tests/unit/test_m5_clustering_discovery.py`, `scripts/demo_m5.py`, `README.md`, `TASKS.md`, `PROJECT_STATE.md` |
| Commands run | `.venv\\Scripts\\python.exe -m pytest tests\\unit\\test_m5_clustering_discovery.py -q`<br>`.venv\\Scripts\\python.exe -m pytest tests\\unit\\test_m5_clustering_discovery.py tests\\ui\\test_app_smoke.py -q`<br>`.venv\\Scripts\\python.exe -m ruff check <M5 changed files>`<br>`.venv\\Scripts\\python.exe scripts\\demo_m5.py` |
| Test result | T35–T38: **4 passed in 2.11s**. M5 plus UI smoke: **8 passed in 3.78s**. Ruff: **All checks passed** for M5 changed files. |
| Manual/demo evidence | Offline seeded blobs run produced experiment `e3a6316b-91d5-4630-8b26-377cc1e7ef7c`: cluster sizes 100/100/100, inertia 31.833647710980145, silhouette 0.7740245866459821 on 300 rows, 10 elbow points, exactly one trial, three stored artifact paths. Tree and kNN meshes were 180×180; K-Means playground produced four requested clusters. |
| Known defects | Full-project Ruff is not yet clean because unfinished M4 files/tests contain lint and contract issues identified by audit. M6 must resolve those before final release claims. Browser screenshot capture and laptop-resolution manual inspection remain M6 work. |
| Environment | Python 3.12.10, Streamlit 1.64.0, pandas 3.0.6, scikit-learn 1.9.1, NumPy 2.5.3, Plotly 7.1.0, Windows 11. |
| Decision changes | None. Elbow sweep is persisted inside `clustering_diagnostics.json`; the UI draws the real plot from that artifact rather than storing duplicate trial IDs. |
| Next smallest task | M6 final verification: repair outstanding M4 export defects, run the entire suite/lint/fresh setup, inspect laptop UI, and document performance and limitations. |

| Field | Record actual evidence |
|---|---|
| Date and milestone | 2026-09-24 • M6 — Final verification and academic demo |
| Implemented/fixed behavior | Repaired M4 target/split/scorer/feature-bound defects; reports now derive from stored facts, escape HTML, include real development permutation rows, failures, holdout exposure, environment and hashes. Model ZIP now contains the required lowercase-manifest bundle and trusted-joblib warning. T34 invokes production CSV escaping. T39 centralizes dataset/project draft invalidation and scopes displayed results to the selected dataset. Demo generators now match `DEMO_AND_EVALUATION` (500×6 regression and 600×4 blobs). |
| Commands run | `.venv\\Scripts\\python.exe -m pytest -q`<br>`.venv\\Scripts\\python.exe -m ruff check .`<br>`.venv\\Scripts\\python.exe scripts\\verify_environment.py`<br>`.venv\\Scripts\\python.exe scripts\\smoke_demo.py`<br>`.venv\\Scripts\\python.exe scripts\\demo_m2.py`<br>`$env:PYTHONIOENCODING='utf-8'; .venv\\Scripts\\python.exe scripts\\demo_m3_mvp.py`<br>`.venv\\Scripts\\python.exe scripts\\demo_m5.py`<br>`.venv\\Scripts\\python.exe scripts\\final_verification.py`<br>Streamlit loopback launch on port 8501 and HTTP request. |
| Test result | **74 passed in 10.26s**; Ruff **all checks passed**; UI suite **5 passed in 3.12s**; Streamlit returned HTTP 200. Required T01–T44 are represented, including new T39 coverage. |
| Performance evidence | Windows 11, Python 3.12.10, AMD64 12 logical CPUs. Iris import/profile: **0.0386 s**, peak `tracemalloc` **0.5115 MiB**. Baseline + three-model Iris experiment: **3.3684 s**, peak `tracemalloc` **0.8411 MiB**. Both performance goals passed on this machine. |
| Academic result | Experiment `0d3203c3-fc84-465d-8e66-3ea90910af78`; selected logistic regression; macro-F1 CV **0.957971 ± 0.026772**; dummy baseline **0.166667**; finalized holdout macro-F1 **0.933333**; holdout previously exposed `false`. |
| Downloaded report example | `storage/exports/0d3203c3-fc84-465d-8e66-3ea90910af78_report.html`; structured evidence: `storage/exports/m6_final_evidence.json`. |
| Completed requirements | All P0/P1 functional requirements have implemented paths and automated/service evidence. Environment verification, offline demos, persistence, exports, prediction, clustering and playground demonstrations completed. |
| Partial requirements | NFR-08 laptop presentation was assessed through Streamlit AppTest and successful local HTTP launch, but no exact 1366×768 browser screenshot was captured. Demo logs and real report exist, but final browser screenshots were not created in this CLI environment. |
| Missing requirements | No known missing P0/P1 implementation requirement. No user study was conducted or claimed. |
| Limitations | Local single user; bounded tabular data; synchronous CPU fits; no grouped/time-series validation; limited registry; no causal explanation; PCA display-only; exposed holdout remains exposed; `tracemalloc` is not whole-process RSS. |
| Next step | Manual evaluator walkthrough at 1366×768 and screenshot capture, without source changes. |

Append completed session records below; preserve prior evidence. Never mark a task complete based only on code existing or an agent claiming it should work.
