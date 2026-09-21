# Ten-week implementation roadmap

Estimate: 8–12 focused hours/week with basic Python knowledge. Actual speed depends on learning and debugging. Complete each gate before adding the next feature. Weeks indicate planned effort, not claims of completed work.

| Week | Milestone | Implement | Gate / concrete demonstration |
|---|---|---|---|
| 1 | M0 — foundation | Environment, dependency lock, package skeleton, contracts, SQLite migration, app navigation, project creation | App opens; project survives restart; migration runs twice safely |
| 2 | M1 — datasets | CSV validation, immutable storage, offline demos, structural profile, role suggestions | Iris and synthetic demos load; malformed/BOM/oversize cases handled |
| 3 | M2a — modeling protocol | Target/roles, row policy, exact split manifests, development EDA, ColumnTransformer/Pipeline | Target never enters X; holdout excluded from fitting and analytic EDA |
| 4 | M2b — supervised engine | Baselines, classification/regression registry, fold-local CV, metrics, CV selection | Iris and synthetic regression produce real comparable CV results |
| 5 | M3a — persistence | Trials, errors, models, metadata, history, locks, idempotency, crash recovery | Restart restores records; duplicate submit does not duplicate a run |
| 6 | M3b — usable MVP | Finalization, compatible comparison, saved model prediction, batch schema checks | End-to-end upload/train/finalize/restart/predict walkthrough passes |
| 7 | M4 — explain/export | Permutation diagnostic, report, experiment/model ZIP, checksum checks | Downloaded report matches DB; reloaded trusted model predictions match |
| 8 | M5a — clustering | Numeric K-Means pipeline, elbow, silhouette guards, PCA visualization | Blobs generate clusters and metrics; invalid k/silhouette handled |
| 9 | M5b — discovery | Algorithm cards, 2D tree/kNN playground, clustering controls, UI polish | Parameter change visibly changes actual model behavior |
| 10 | M6 — delivery | Edge cases, UI checks, resource measurements, fresh setup, user guide and demo evidence | All v1 gates reviewed; actual test/benchmark evidence recorded |

## Gate details

### M0: a stable place to build

Create only the foundation required for the later workflow. Future pages may show an honest 'Not implemented yet' panel, but no fabricated metrics or inactive controls pretending to work. Produce a tested setup command and identify the selected package versions. Evidence: environment, migration test and app launch.

### M1: trustworthy dataset ingestion

Implement the data contract before training. Create synthetic fixtures for missing values, mixed types and encoding issues. Save immutable uploaded bytes and parser config. Evidence: validation cases T02–T07 and demo source metadata.

### M2: correct ML engine

Build pure functions first, then wire the experiment page. Complete split/feature/metric checks before adding every algorithm. Start with Dummy + Logistic Regression + Decision Tree classification; add regression and the remaining registry. Evidence: fold manifests, leakage tests, real score output and model-selection reasoning.

### M3: end-to-end MVP

Wire persistence, finalization and prediction. Stop adding new features until the same model is usable after server restart. Evidence: full MVP demo, compatibility rejection, crash/duplicate handling and prediction roundtrip.

### M4: explainable, exportable evidence

Generate reports from stored records, not current widget values. Include failures, data-cleaning counts and holdout exposure. Evidence: archive integrity and report-to-DB cross-check.

### M5: interactive discovery

Clustering is unsupervised and uses its own score vocabulary. Playground results remain separate from formal comparisons. Evidence: invalid silhouette guard and at least two parameter changes with explanatory text.

### M6: demonstrable completion

Run the complete required test suite once all features land, resolve remaining real risks, record outputs, and update progress honestly. Evidence: screenshots, test log, measured timings, package lock and final walkthrough.

## Weekly work rhythm

Read current state → select one milestone slice → implement a vertical path → run relevant tests → use it in browser → fix defects → update TASKS/PROJECT_STATE with evidence. Each week should end with something demonstrable.

## If the deadline is shorter

For a 4–6 week submission, deliver M0–M3 well, then add one playground if time permits. Mark clustering/explanation/export as future work if not implemented. Do not weaken split correctness, persistence or real evaluation to fit more features. Revised scope must be recorded in PRD and PROJECT_STATE.

## Optional team allocation

If four people are available: member 1 owns UI/discovery, member 2 ingestion/EDA, member 3 ML/evaluation, member 4 persistence/tests/export. These are suggested human roles, not assumed team size. Agree on SERVICE_CONTRACTS before parallel edits; integrate every week. A solo developer follows milestone order.
