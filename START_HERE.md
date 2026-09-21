# DataMind — Start Here

**An Interactive Machine Learning Discovery & Experimentation Platform**  
Planning pack v1.0 • Prepared 21 September 2026

## Ye project kya karega?

DataMind ek browser-based ML lab hoga. User CSV dataset upload karega, data samjhega, prediction target choose karega, preprocessing configure karega aur multiple machine learning models train karke results compare karega. Saved model se new data par prediction aur downloadable experiment report milega. Algorithm Explorer aur Playground mein user parameters change karke ML concepts practically samjhega.

**Example:** Iris flower dataset load karo → target `species` choose karo → Logistic Regression, Decision Tree aur Random Forest train karo → cross-validation results compare karo → selected model ka held-out test result dekho → flower measurements enter karke prediction lo.

Ye **implementation specifications aur prompts** ka pack hai. Working application, trained models ya completed test results abhi included nahi hain. Antigravity ko in files ke according code implement karna hai.

## Proposed scope and assumptions

- Academic project; one developer can follow the plan, a team can divide modules.
- Windows laptop, Python 3.11 development target, browser UI, local single-user workspace.
- CPU-based tabular ML. Core runtime ko paid API, GPU, Docker, cloud account ya downloaded LLM ki zarurat nahi.
- First working MVP: classification and regression. Full v1 adds K-Means clustering, explanations, reports and educational playgrounds.
- Planning estimate: 10 weeks, roughly 8–12 focused hours/week for someone comfortable with basic Python. It is an estimate, not a deadline commitment.
- Streamlit is the selected UI for this pack. React + FastAPI is a future migration option, not a second simultaneous implementation.
- Upload limits start at 10 MiB, 20,000 rows and 100 raw columns; these are product limits to implement, not measured capacity claims.

## Implement kya karna hai?

| Module | User kya kar payega? | Release |
|---|---|---|
| Dataset workspace | CSV upload, Iris/synthetic demos, history | MVP |
| Data discovery / EDA | Missing values, distributions, class balance, correlations | MVP |
| Experiment setup | Target, features, preprocessing, models, split and seed choose karna | MVP |
| ML engine | Classification/regression train aur cross-validation | MVP |
| Experiment comparison | Comparable runs ke real metrics aur timings dekhna | MVP |
| Saved prediction | Same fitted pipeline se single/batch prediction | MVP |
| Explain and export | Permutation importance, report, model bundle | Full v1 |
| Clustering lab | K-Means, elbow, silhouette, cluster visualization | Full v1 |
| Algorithm discovery | Algorithm cards, decision boundaries, parameter experiments | Full v1 |

## Technology choices

| Layer | Choice | Why this project uses it |
|---|---|---|
| Browser UI | Streamlit | Python se interactive multi-page app; less frontend setup |
| Data preparation | pandas, NumPy | Tables, type handling and transformations |
| ML | scikit-learn | Pipelines, algorithms, validation and metrics |
| Interactive charts | Plotly | Hover, zoom and selectable chart controls |
| Persistent metadata | SQLite through standard `sqlite3` | Datasets, experiments, trials and metric history |
| Local artifacts | Versioned files + joblib | Raw datasets, split manifests and fitted pipelines |
| Validation/testing | Pydantic, pytest, Streamlit AppTest | Typed configs, ML invariants and UI smoke checks |
| Concurrency guard | filelock | One training/finalization operation at a time |

## Antigravity mein use kaise karein?

1. ZIP extract karo. Inner folder `DataMind_Antigravity_Pack` ko optionally `DataMind` rename karo.
2. Antigravity mein **isi folder ko project root ke roop mein open karo**.
3. [ANTIGRAVITY_START_PROMPT.md](ANTIGRAVITY_START_PROMPT.md) ka poora prompt agent chat mein paste karo. Ye PowerShell command nahi hai.
4. Agent first milestone implement karega, relevant checks run karega aur [TASKS.md](TASKS.md) / [PROJECT_STATE.md](PROJECT_STATE.md) update karega.
5. Milestone complete hone ke baad [prompts/MILESTONE_PROMPTS.md](prompts/MILESTONE_PROMPTS.md) ka next prompt do. Har milestone ka working result dekho.
6. Nayi conversation mein [prompts/CONTINUE_PROMPT.md](prompts/CONTINUE_PROMPT.md) use karo; agent current files aur actual code se resume karega.

Workspace rule file `.agents/rules/datamind.md` included hai. Rules panel mein iska activation **Always on** set/verify kar sakte ho. Automatic discovery par depend mat karo: starter prompt explicitly files padhne ko kehta hai. Antigravity's current official documentation describes `.agents/rules/` and compatibility with older `.agent/rules/` locations. See [official rules documentation](https://antigravity.google/docs/rules-workflows).

## Files kis kaam ki hain?

| File | Purpose |
|---|---|
| [PRD.md](PRD.md) | Problem, objectives, scope, requirements and acceptance criteria |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Components, data flow, execution and persistence decisions |
| [ROADMAP.md](ROADMAP.md) | Ten-week sequence, milestone gates and demo evidence |
| [FILE_STRUCTURE.md](FILE_STRUCTURE.md) | Files/modules Antigravity should create and responsibilities |
| [AGENTS.md](AGENTS.md) | Coding and ML implementation rules |
| [TASKS.md](TASKS.md) | Actionable implementation checklist |
| [PROJECT_STATE.md](PROJECT_STATE.md) | Honest progress and handover record |
| [docs/ML_SPEC.md](docs/ML_SPEC.md) | Leakage prevention, algorithms, metrics and selection protocol |
| [docs/DATA_CONTRACTS.md](docs/DATA_CONTRACTS.md) | CSV validation, schemas, errors and resource limits |
| [docs/DATABASE.md](docs/DATABASE.md) | Table meanings, lifecycle, consistency and versioning |
| [docs/schema.sql](docs/schema.sql) | Initial executable SQLite schema specification |
| [docs/SERVICE_CONTRACTS.md](docs/SERVICE_CONTRACTS.md) | Internal Python service interfaces and DTOs |
| [docs/UI_SPEC.md](docs/UI_SPEC.md) | Pages, user actions, empty/loading/error states |
| [docs/TEST_PLAN.md](docs/TEST_PLAN.md) | Concrete tests, inputs and expected results |
| [docs/SETUP_WINDOWS.md](docs/SETUP_WINDOWS.md) | Environment and eventual run commands |
| [docs/DEMO_AND_EVALUATION.md](docs/DEMO_AND_EVALUATION.md) | Demo sequence, academic contribution and evidence |
| [docs/DECISIONS_AND_RISKS.md](docs/DECISIONS_AND_RISKS.md) | Assumptions, trade-offs and future extensions |
| [docs/SOURCES.md](docs/SOURCES.md) | Official documentation behind technical choices |
| [prompts/MILESTONE_PROMPTS.md](prompts/MILESTONE_PROMPTS.md) | Build instructions for each milestone |
| [prompts/CONTINUE_PROMPT.md](prompts/CONTINUE_PROMPT.md) | Resume an interrupted development session |
| [prompts/REVIEW_PROMPT.md](prompts/REVIEW_PROMPT.md) | Review implementation against the specifications |
| [examples/classification_config.json](examples/classification_config.json) | Illustrative supervised experiment configuration |
| [examples/clustering_config.json](examples/clustering_config.json) | Illustrative K-Means configuration |

## First successful version kaisa dikhega?

Browser mein app khule; Iris load ho; real models train ho; baseline aur CV metrics SQLite mein save hon; app restart ke baad experiment wapas mile; selected model valid input par prediction de. **Sirf attractive dashboard, dummy charts ya fabricated accuracy ko project complete mat maano.**

Dependency versions implementation ke samay resolve, test aur lock karne hain. This pack does not claim that a particular set of package versions has been installed or tested.
