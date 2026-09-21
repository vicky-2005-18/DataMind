# Verification and acceptance plan

This is the test plan to implement. **No application test is claimed to have run in this planning pack.** Add tests around meaningful boundaries and ML correctness; avoid asserting implementation details just to inflate coverage.

## Fixtures

Use offline Iris; seeded `make_regression`; seeded `make_blobs`; small in-memory CSVs for edge cases; synthetic mixed numeric/categorical classification with missing values. No private datasets. Include enough rows/classes for configured validation; tiny fixtures can test ingestion without entering training.

## Required tests

| ID | Input / action | Expected result | Gate |
|---|---|---|---|
| T01 | Initialize DB twice; create/reopen project | Schema idempotent, one migration record, project persists | M0 |
| T02 | Valid CSV and UTF-8-BOM CSV | Same clean headers and values | M1 |
| T03 | Empty/header-only CSV; duplicate trimmed headers; malformed quotes/rows | Specific INVALID_CSV, no registered usable dataset | M1 |
| T04 | At limit and one byte/row/column beyond | Boundary accepted; excess rejected without truncated training | M1 |
| T05 | Mixed types, missing cells, infinity, long strings | Correct roles/warnings; invalid values rejected with location | M1 |
| T06 | Load Iris and seeded synthetic demos offline | No network; metadata and deterministic content recorded | M1 |
| T07 | Reupload changed bytes or different parser settings | New immutable dataset identity/config; old runs unaffected | M1 |
| T08 | Select target among feature roles | Validation rejects target leakage | M2 |
| T09 | Missing target with default then explicit drop policy | Default reject; explicit removal records exact source row IDs | M2 |
| T10 | Duplicate feature/target rows and conflicting targets | Policy collapses exact duplicates; conflicts rejected | M2 |
| T11 | Same data/config/seed twice | Exact same development/test/CV row membership | M2 |
| T12 | Inspect split manifest sets | Train/test disjoint; each dev row validated exactly once across folds | M2 |
| T13 | Classification with rare/one class; invalid split size | Preflight error; no silent unstratified fallback | M2 |
| T14 | Spy transformer records fit row IDs in CV and refit | Every fold fits only its train IDs; final refit only development IDs | M2 |
| T15 | Holdout has extreme numeric values and unseen categories | Fitted imputer/scaler/vocabulary unchanged by holdout | M2 |
| T16 | All-missing numeric/categorical feature in a fold | Deterministic policy, stable transform behavior, no width surprise | M2 |
| T17 | Hand-computed classification and regression arrays | Metrics match independent oracle; RMSE positive, correct direction | M2 |
| T18 | Chosen models compete on one experiment | Identical fold IDs, baseline present, selection uses CV only | M2 |
| T19 | Best CV candidate has worse hypothetical holdout score | Selector still chooses by CV and never reads test result | M2 |
| T20 | One estimator deliberately fails | Trial failure preserved; others complete; no fake zero score | M3 |
| T21 | All real models fail or baseline fails | Overall supervised experiment failed, useful reason stored | M3 |
| T22 | Submit same token twice; another request while lock held | At most one experiment/token; busy request cannot fit concurrently | M3 |
| T23 | Simulate crash, then guarded recovery; separately hold active lock | Stale runs interrupted only when lock free; active run untouched | M3 |
| T24 | Train, close server, restart | History/config/metrics/model restored from durable storage | M3 |
| T25 | Finalize twice | One immutable evaluation; same model/metrics, no refit | M3 |
| T26 | Finalize another experiment on same split | Holdout previously exposed flagged in UI/report | M3 |
| T27 | Compare different dataset, target or fold manifest | Rank rejected with mismatch reason | M3 |
| T28 | Reload saved model and predict same rows | Labels match; numerical predictions within 1e-8 tolerance | M3 |
| T29 | Reordered columns, missing column, extra column, invalid numeric | Reorder accepted; other cases explicit schema handling | M3 |
| T30 | Prediction category absent during fit | Same encoder used; valid prediction plus unseen-category warning | M3 |
| T31 | Missing/corrupt model artifact or incompatible package manifest | MODEL_UNAVAILABLE, no silent retrain or arbitrary file load | M3 |
| T32 | Compute permutation diagnostic on saved champion | Original feature names, fixed sample seed, development label, no causal claim | M4 |
| T33 | Export then inspect manifest/report/ZIP | Checksums valid; records match DB; no absolute paths/raw dataset by default | M4 |
| T34 | HTML-like header and formula-prefixed text in CSV export | Escaped HTML and spreadsheet text; no active injected content | M4 |
| T35 | K-Means on seeded blobs | Finite inertia, cluster sizes sum to n, stored seed and true feature space | M5 |
| T36 | One cluster, too-large k, insufficient distinct points, invalid silhouette sample | Validation or N/A/reason; no invented accuracy | M5 |
| T37 | PCA projection and silhouette calculation | PCA is display-only; metric uses scaled modeling features | M5 |
| T38 | Change tree depth/kNN k in toy playground | Actual fitted output changes on a suitable deterministic fixture | M5 |
| T39 | Change dataset after configuring previous experiment | Draft dependent choices invalidate; old model not silently reused | M6 |
| T40 | Fresh environment + UI walkthrough + measurements | Documented commands work; real evidence and limitations recorded | M6 |
| T41 | Cross-project dataset/split/trial references | Service rejects inconsistent ownership and relationships | M3 |
| T42 | Force filesystem write success then DB failure | Orphan is not loadable; recovery leaves previous records intact | M3 |
| T43 | Constant regression target or undefined AUC input | Reject unsupported target or show null/reason for undefined metric | M2 |
| T44 | High-cardinality one-hot transformation beyond cap | Fails before oversized allocation; suggests feature reduction | M2 |

## Independent metric oracles

- Regression: y_true=[0,2], y_pred=[0,0] → MAE=1, MSE=2, RMSE=sqrt(2), R²=-1. This unit fixture bypasses dataset minimum-row rules.
- Classification: true=[0,0,1,1], predicted=[0,1,1,1] → accuracy=0.75, macro F1=(2/3+4/5)/2=11/15. Check confusion matrix [[1,1],[0,2]].
- CV leakage test must inspect fit calls or learned quantities, not just check that an object is named Pipeline.
- Baseline expectations come from its actual strategy/training fold, not a hardcoded dataset accuracy.

## Manual MVP walkthrough

Create project → load Iris → confirm classification/target → prepare split → explore development data → train three models → inspect baseline/CV → finalize champion → make one prediction → restart server → reopen run/predict again → compare compatible clone → reject an incompatible comparison.

Full v1 extends this with export, explanation, synthetic regression, blobs clustering and parameter playground.

## Evidence format

Record command, date, Python/package versions, fixture ID/seed, actual result, test counts and log path. Performance record includes hardware, input size, elapsed time and peak memory when measured. A failed target is reported as a failed target, not silently redefined. Screenshot labels must distinguish sample mockups from real runs; final evidence must use actual application output.

## Release gate

Required tests implemented/passing; no unresolved critical data leakage, persistence, prediction schema or fabricated-output defect; clean setup and demonstration repeatable. Broaden tests only to cover a concrete missing behavior or observed regression.
