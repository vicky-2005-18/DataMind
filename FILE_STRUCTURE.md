# Planned repository structure

This pack already contains specifications, prompts, examples, rules and configuration examples. Application modules below are **to be created by Antigravity**. Do not confuse this map with an existing working application.

| Path | Responsibility |
|---|---|
| `app.py` | Streamlit entry point, page registration and shared shell |
| `pyproject.toml` | Package metadata, direct dependencies and tooling configuration |
| `requirements.lock.txt` | Resolved/tested runtime dependency versions |
| `requirements-dev.lock.txt` | Resolved/tested test/lint dependency versions |
| `.streamlit/config.toml` | Local server address, theme and upload limit |
| `datamind/__init__.py` | Package and version |
| `datamind/config.py` | Validated settings, paths and resource budgets |
| `datamind/contracts.py` | Versioned request/result/error models |
| `datamind/ui/navigation.py` | Page list and current project/dataset context |
| `datamind/ui/components.py` | Reusable cards, state messages and metric formatting |
| `datamind/ui/pages/home.py` | Project selection and actual recent activity |
| `datamind/ui/pages/datasets.py` | Upload/demo/profile/role selection |
| `datamind/ui/pages/explore.py` | Development EDA and chart controls |
| `datamind/ui/pages/experiments.py` | Experiment form, progress, CV and finalization |
| `datamind/ui/pages/compare.py` | Comparison checks and consistent metric table |
| `datamind/ui/pages/predict.py` | Single/batch inference |
| `datamind/ui/pages/explain_export.py` | Model diagnostics and export actions |
| `datamind/ui/pages/clustering.py` | K-Means lab |
| `datamind/ui/pages/discover.py` | Algorithm cards and playground |
| `datamind/services/projects.py` | Project orchestration |
| `datamind/services/datasets.py` | Import/demo/profile orchestration |
| `datamind/services/experiments.py` | Supervised orchestration and finalization |
| `datamind/services/comparison.py` | Cohort compatibility and sorting |
| `datamind/services/prediction.py` | Input schema validation and saved inference |
| `datamind/services/explanations.py` | Bounded diagnostic calculation |
| `datamind/services/clustering.py` | Unsupervised orchestration |
| `datamind/services/reports.py` | Report/export generation |
| `datamind/services/recovery.py` | Guarded interruption and artifact recovery |
| `datamind/data/ingestion.py` | CSV byte validation and parsing |
| `datamind/data/profiling.py` | Counts/types/quality summary |
| `datamind/data/demos.py` | Iris and seeded synthetic generation |
| `datamind/data/views.py` | Roles, row policy and modeling-view fingerprints |
| `datamind/ml/registry.py` | Algorithm factories, allowed parameters and descriptions |
| `datamind/ml/preprocessing.py` | Unfitted transformers and pipeline construction |
| `datamind/ml/splitting.py` | Exact split/fold manifests |
| `datamind/ml/training.py` | CV, trial handling and development refit |
| `datamind/ml/metrics.py` | Metric definitions, directions and undefined cases |
| `datamind/ml/clustering.py` | K-Means, elbow and silhouette |
| `datamind/ml/explain.py` | Permutation importance |
| `datamind/ml/playground.py` | Toy generators and decision meshes |
| `datamind/storage/database.py` | Connections and migration runner |
| `datamind/storage/repositories.py` | Parameterized data access and invariant checks |
| `datamind/storage/artifacts.py` | Safe paths, hashes and atomic file writes |
| `datamind/storage/locks.py` | Single workspace execution lock |
| `datamind/storage/migrations/001_initial.sql` | Versioned implementation of docs/schema.sql |
| `datamind/reports/templates/experiment.html` | Escaped report template |
| `datamind/content/algorithms.json` | Reviewed educational text and parameter explanations |
| `tests/unit/` | Parsing, split, config, metric and preprocessing checks |
| `tests/integration/` | Persistence, training, prediction and export workflows |
| `tests/ui/` | Streamlit AppTest smoke tests |
| `tests/fixtures/` | Small synthetic edge-case inputs only |
| `scripts/verify_environment.py` | Print environment and dependency compatibility evidence |
| `scripts/smoke_demo.py` | Small reproducible end-to-end demo through services |
| `storage/` | Generated local data, database, splits, models and reports; gitignored |
| `logs/` | Local diagnostics without raw user data; gitignored |

Use normal Python packages with `__init__.py` as needed. Keep UI pages under the explicit navigation system; do not accidentally combine two competing Streamlit page-discovery mechanisms. Start with small modules and introduce them as the milestones need them. Avoid a giant `app.py` containing all ML/SQL logic.

The future implementation README should link back to START_HERE, document tested commands, and distinguish implemented functionality from planned work.
