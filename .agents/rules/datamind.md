# DataMind workspace rule

Use this as a workspace rule; select Always on in the Antigravity Rules panel if available. The startup prompt also explicitly loads the canonical files, so this rule is not the only context source.

Read AGENTS.md and PROJECT_STATE.md before implementing. Follow PRD.md, ARCHITECTURE.md, ROADMAP.md and the relevant docs specifications. Respect the user's later explicit changes and keep the documents consistent.

DataMind v1 uses Python, Streamlit, scikit-learn, pandas, Plotly, SQLite and a local artifact store. It is a local single-user tabular ML application. Build milestone by milestone with real outputs and bounded resources.

Critical invariants: target excluded from X; development/test separation; preprocessing fitted inside CV; same folds for model comparison; CV-based selection; explicit holdout finalization; baseline included; saved pipeline reused for prediction; configs/seeds/versions persisted; SQLite history survives restart; no fabricated metrics.

Keep UI/services/ML/storage separate. No arbitrary model uploads or user code execution. Avoid unrequested cloud, React, LLM and distributed-system scope. Protect existing files. Keep TASKS.md and PROJECT_STATE.md updated with observed verification evidence. Do not assert implementation completion from the planning documents alone.
