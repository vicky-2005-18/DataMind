# DataMind — Product Requirements Document

Version 1.0 • Status: proposed build specification • 21 September 2026

## 1. Problem and product definition

Students often learn ML algorithms in isolated notebooks. They struggle to connect dataset quality, preprocessing, algorithm choice, hyperparameters and evaluation. Comparing notebook runs is difficult when settings and data splits are not recorded.

DataMind is a local interactive ML learning and experimentation application. It guides users from a tabular dataset to a reproducible experiment, explains the result, and preserves enough information to compare and repeat the work.

**Product promise:** explore data, understand model choices, run real experiments and explain what the measured results mean.

## 2. Users and outcomes

| User | Need | Successful outcome |
|---|---|---|
| ML student | Learn how a choice changes behavior | Changes a parameter and sees real chart/metric changes |
| Project developer | Compare several models consistently | Reopens stored settings, CV scores and selected model |
| Faculty evaluator | Inspect methodology and evidence | Sees baseline, split protocol, limitations and working demo |

Goals: accessible experimentation; correct evaluation; persistent experiment history; understandable visualization; reproducible local demonstration. No fixed accuracy percentage is a product requirement.

## 3. Scope and release boundaries

**MVP (M0–M3 / weeks 1–6):** local workspace, validated CSV/demo loading, dataset profile, development-data EDA, classification, regression, safe preprocessing, fixed holdout plus CV, baseline comparison, saved champion pipeline, history and prediction.

**Full v1 (M4–M6 / weeks 7–10):** permutation importance, portable experiment export, HTML/Markdown report, bounded K-Means lab, algorithm cards, interactive playground, regression/edge-case tests and demo evidence.

**Deferred:** login and multi-user permissions, cloud deployment, REST API, React frontend, deep learning, NLP/image datasets, forecasting, grouped/longitudinal modeling, distributed compute, arbitrary Python execution, external model imports, LLM chat, automatic internet dataset scraping, large-scale AutoML, SHAP and advanced hyperparameter search. Add these only through a documented scope revision.

## 4. Functional requirements

Priority P0 = MVP; P1 = required for full v1; P2 = future.

| ID | Priority | Requirement | Acceptance |
|---|---|---|---|
| FR-01 | P0 | Create/select local project | Unique project ID persists across app restart |
| FR-02 | P0 | Import UTF-8/UTF-8-BOM CSV | Valid table is saved; invalid or oversize data gets actionable error |
| FR-03 | P0 | Provide offline demo datasets | Iris, seeded synthetic regression and blobs require no runtime fetch |
| FR-04 | P0 | Show dataset profile | Row/column counts, types, missingness and duplicate counts match input |
| FR-05 | P0 | Confirm task, target and feature roles | Target excluded from X; incompatible task is blocked |
| FR-06 | P0 | Explore development data | Histograms, category counts, scatter and numeric correlation work |
| FR-07 | P0 | Configure preprocessing | Imputation, encoding and scaling persisted as unfitted configuration |
| FR-08 | P0 | Train compatible algorithms | Baseline plus at least one real model evaluated using the same folds |
| FR-09 | P0 | Report task-specific metrics | Classification and regression use their own metrics and directions |
| FR-10 | P0 | Select champion by CV | Holdout stays hidden until explicit finalization of selected trial |
| FR-11 | P0 | Persist experiments and failures | Restart preserves config, versions, status, scores and error reason |
| FR-12 | P0 | Compare compatible experiments | Mismatched dataset/task/splits cannot share a ranked leaderboard |
| FR-13 | P0 | Predict from saved local model | Same fitted preprocessing handles single row and validated CSV batch |
| FR-14 | P1 | Explain selected model | Original-feature permutation importance is labeled non-causal |
| FR-15 | P1 | Export results | Report and ZIP contain actual config/metrics, model and manifest |
| FR-16 | P1 | Explore K-Means clusters | Numeric input, k controls, inertia, valid silhouette and 2D plot |
| FR-17 | P1 | Browse algorithm cards | Each supported family has task, intuition, limits and parameter guide |
| FR-18 | P1 | Use educational playground | Seeded 2D samples; tree/kNN boundaries and K-Means controls update |
| FR-19 | P0 | Prevent duplicate submissions | One submit token causes at most one experiment; training lock enforced |
| FR-20 | P0 | Mark invalid/unavailable results | Undefined metric is null with reason; never fake zero/accuracy |

## 5. Core user stories

1. As a student, I load Iris and train a classifier without writing training code.
2. As a learner, I compare an unscaled and scaled kNN pipeline under identical folds and explain the difference.
3. As a developer, I return tomorrow and retrieve an experiment's exact configuration and model.
4. As an evaluator, I can tell which scores came from cross-validation and which came from the holdout.
5. As a learner, I vary tree depth on generated data and inspect overfitting behavior.
6. As a user, I receive a column-specific fix when my prediction CSV does not match the training schema.

## 6. Nonfunctional requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR-01 | Local CPU runtime; no API key for core functions | Offline demos after dependencies are installed |
| NFR-02 | Deterministic seeds and recorded environment | Repeated config yields same splits and numerically close scores |
| NFR-03 | Persistent history independent of browser state | Restart test with SQLite and artifacts preserved |
| NFR-04 | Bounded resources | Enforce limits from DATA_CONTRACTS; run one training operation at a time |
| NFR-05 | Clear operation state | Working stage and elapsed time shown; errors preserve input config |
| NFR-06 | Maintainable layers | UI imports services; ML layer works without Streamlit |
| NFR-07 | Honest reporting | Every displayed metric links to a stored trial/evaluation |
| NFR-08 | Usable at laptop resolution | 1366×768 smoke check, readable tables, no color-only meaning |
| NFR-09 | Local input handling | No raw data in logs; no uploaded executable/pickle model loading |
| NFR-10 | Durable writes | Atomic artifact publication plus recoverable DB lifecycle |

Performance goals, to measure in M6: demo profile under 3 seconds and default Iris three-model experiment under 60 seconds on the developer's recorded laptop. These are targets, not existing benchmark results. The maximum supported CSV can take longer; report measured elapsed time and failure conditions.

## 7. Workflow rules

- Initial full-dataset screen is limited to structural quality/profile information. After supervised split creation, analytical charts and previews default to development rows. This reduces accidental use of holdout information during model design.
- User explicitly confirms classification/regression; numeric targets are never automatically treated as regression without confirmation.
- Datasets with time dependence or repeated entities require a different validation design and are outside v1 supported modeling.
- Model selection uses CV on development rows. Finalization records the selected trial and evaluates its saved development-fitted pipeline on the held-out test rows.
- Freeze an experiment after finalization. Additional tuning after seeing holdout results must be labeled as reusing an exposed holdout; do not present that score as untouched evidence.
- Educational synthetic playground results remain distinct from dataset experiment history.

## 8. Definition of done

All P0/P1 criteria demonstrated, required tests passing, clean-environment setup recorded, no fabricated results, no active critical leakage defect, report/export/prediction validated, and PROJECT_STATE accurately updated. The evaluator can complete the walkthrough in DEMO_AND_EVALUATION without editing application source.

## 9. Traceability

FR-01–04 → M0/M1; FR-05–10 → M2; FR-11–13 and FR-19 → M3; FR-14–15 → M4; FR-16–18 → M5; FR-20 and NFRs → throughout, with M6 evidence. Detailed expected outcomes are in [docs/TEST_PLAN.md](docs/TEST_PLAN.md).
