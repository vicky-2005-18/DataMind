# ML implementation specification

## 1. Supported tasks and registry

Use an allowlisted registry with explicit task, estimator factory, supported parameters, defaults, limits and explanatory text. Instantiate a new estimator for every fit. Reject unknown algorithm IDs/parameters.

| Task | ID / estimator | Starting defaults | UI controls |
|---|---|---|---|
| Classification baseline | `dummy_classifier` / DummyClassifier | strategy=`most_frequent` | None |
| Classification | `logistic_regression` / LogisticRegression | C=1, max_iter=1000 | C: 0.01, 0.1, 1, 10 |
| Classification | `decision_tree_classifier` / DecisionTreeClassifier | max_depth=5, seed=42 | depth 1–20, min_samples_leaf 1–20 |
| Classification | `random_forest_classifier` / RandomForestClassifier | n_estimators=100, max_depth=10, n_jobs=1, seed=42 | trees 50–200, depth 2–20 |
| Classification | `knn_classifier` / KNeighborsClassifier | n_neighbors=5, weights=`uniform` | k 1–25, weights uniform/distance |
| Regression baseline | `dummy_regressor` / DummyRegressor | strategy=`mean` | None |
| Regression | `linear_regression` / LinearRegression | default settings, n_jobs=1 | None |
| Regression | `ridge` / Ridge | alpha=1 | alpha: 0.01, 0.1, 1, 10, 100 |
| Regression | `decision_tree_regressor` / DecisionTreeRegressor | max_depth=5, seed=42 | depth 1–20, min_samples_leaf 1–20 |
| Regression | `random_forest_regressor` / RandomForestRegressor | n_estimators=100, max_depth=10, n_jobs=1, seed=42 | trees 50–200, depth 2–20 |
| Clustering | `kmeans` / KMeans | k=3, n_init=10, max_iter=300, seed=42 | k 2–10 |

Up to four selected nonbaseline models per supervised experiment. Baseline is always added. No parameter search in MVP; the user can clone the experiment and change bounded settings. Use the experiment seed for estimators that support it. Set thread limits before importing numerical libraries.

## 2. Modeling view and split protocol

1. Validate the raw table and keep the original file immutable.
2. User confirms task, target, feature allowlist, types and that rows represent independent observations.
3. Reject missing target values by default. An explicit `drop_missing_target=true` can remove them, recording counts and retained original row IDs; target values are never imputed.
4. Reject identical selected feature vectors with conflicting targets; ask the user to resolve ambiguous records. Collapse duplicate `(selected features + target)` rows only with the documented `drop_exact_duplicates` setting. Preserve a mapping from retained row to source rows. All row membership changes go into a new modeling-view fingerprint.
5. Minimum 30 eligible rows. Classification: 2–20 classes, at least 10 rows per class before splitting. Regression: finite numeric target with at least two distinct values. Refuse empty feature set.
6. Default development/test = 80/20, seed 42. Optional test fractions are 0.20 and 0.25. Classification uses stratified splitting, regression shuffled splitting. Verify both class support and resulting split size; error instead of silently using an unstratified fallback.
7. On development rows, use 5-fold `StratifiedKFold` for classification or shuffled `KFold` for regression, both with the stored seed. A requested 3-fold option is allowed. Check minimum class count and smallest training-fold size before fitting.
8. Persist **explicit original row IDs for each split and each CV fold**. Every competing model receives these exact folds. Reject kNN k greater than the smallest training-fold sample count.

Split ID is reusable when dataset version, task, target, eligible row IDs, test fraction, seed and CV configuration match. Fingerprint the actual row memberships as well as config. Feature changes may be compared only if they leave the same eligible rows and split manifest; otherwise show a separate cohort. Target, ID-like fields and user-excluded columns never enter X.

## 3. Preprocessing pipeline

`Pipeline([('preprocess', ColumnTransformer(...)), ('model', estimator)])`

| Column role | Steps | Options / guard |
|---|---|---|
| Numeric | SimpleImputer → scaler | median default or mean; StandardScaler default, MinMaxScaler or passthrough |
| Categorical / boolean | Missing-value fill → OneHotEncoder | Normalize nonmissing values to strings; constant missing token; handle_unknown=`ignore`; bounded category count |
| Target | Separate from X | No feature transformer fits on y |
| ID / unsupported datetime / free text | Exclude explicitly | User sees reason; no silent arbitrary encoding |

Use dense output for this bounded v1, with a maximum of 500 transformed columns and 10 million transformed cells. Estimate/check before allocation; reject with instructions to exclude high-cardinality features. Numeric all-missing columns get a deterministic fill (e.g. zero using a documented custom transformer or supported imputer option) and a warning; never allow an estimator to receive an unexpected disappearing column. A configured missing category token must be escaped if it collides with real values.

Encoders/scalers/imputers are fitted **inside each CV fold** and then on development rows for the saved pipeline. Dataset profiling may inspect raw types/missingness; it does not produce a fitted transformer. Use selected roles fixed by user configuration, with train-fitted category vocabularies. Tree models can accept scaled input; UI explains scaling is most relevant to distance and linear models.

Do not add SMOTE, feature selection, PCA for supervised training, or automatic outlier removal in v1. If later added, fit them within CV, document how validation rows are handled and update leakage tests.

## 4. Supervised metrics and selection

| Task | Primary selection metric | Other metrics | Display rules |
|---|---|---|---|
| Classification | Macro F1, maximize | Accuracy, balanced accuracy, macro precision/recall; optional valid binary ROC-AUC | 0–1 values; macro averaging and class support explicit |
| Regression | RMSE, minimize | MAE, R² | RMSE/MAE in target units; R² can be negative |

Use macro metrics with `zero_division=0` and show a warning when a class has no predicted positives. Confusion matrix has rows=true, columns=predicted and stored class order. Binary ROC-AUC requires an explicit positive class, both classes present and probabilities/scores. If undefined, use null plus reason. Multiclass AUC and multiclass ROC are deferred.

CV result includes every fold score, arithmetic mean and population standard deviation (`ddof=0`). Standard deviation is fold variation, not a confidence interval. If sklearn scoring returns negative errors, invert only the error scores before persistence/display; model selection minimizes positive RMSE. Use the selected installed sklearn API for RMSE and verify against a hand-computed fixture.

Selection order: primary CV mean; on equal values within 1e-12, prefer the lower model complexity order documented in the registry; then algorithm ID. The baseline participates; if it is best, show it as the recommendation and state that no selected model improved the primary CV score. Retain all successful trials for inspection.

Each model gets a fresh pipeline. Capture warnings and duration. A failed model does not erase another model's result; list its exception code and user-safe message. A failed fold makes that trial failed, rather than averaging a partially successful CV as though complete.

## 5. Champion persistence and holdout

After CV selection, refit the chosen pipeline on all development rows and save it. Other successful trials may be persisted too; never display a model as available for prediction without its artifact. Store the exact feature order, types, model parameters, dataset/split IDs, seeds, package versions and source commit when available.

`finalize_experiment(experiment_id)` is an explicit action, protected by lock and idempotency. It freezes the selected trial, scores it on holdout and saves an evaluation with unique `(experiment_id, scope='holdout')`. Repeated finalization returns the same result, without training or producing additional evaluations.

If a prior evaluation exists for the same split fingerprint, disclose **holdout previously exposed** before a new experiment finalizes, and record this flag in the report. Repeated experimentation after seeing a holdout reduces its independence; a new random split of the same already-inspected data is not guaranteed to restore an untouched evaluation. No leaderboard sorts by holdout scores.

The saved prediction model is the development-fitted pipeline that produced the holdout score. Training a deployment model on all data is future scope and would require a different artifact with different evidence.

## 6. Comparison and reproducibility

Rank only completed experiments sharing dataset hash/parser version, modeling rows, task, target, split/fold fingerprint, primary metric and metric-definition version. Feature/preprocessing differences may be the subject of comparison but must be visible. Incompatible selections get `INCOMPATIBLE_COMPARISON` with the differing fields.

Clone config into a new experiment ID. Save source config hash, environment version, algorithm registry version and seed. Same-environment reruns should have the same row membership and scores within stated numeric tolerances; do not promise byte-identical model files or durations across operating systems/library versions.

## 7. Explainability

For the saved champion, compute permutation importance on development rows as an explicitly labeled **development-set diagnostic**, using the full pipeline so importances correspond to original input columns. This is not independent evaluation and is not causal evidence. Use the primary scoring rule, seed 42, 5 repeats, at most 50 features and a seeded sample of 500 rows. Display mean change and variation; negative values are legitimate. Warn that correlated features can obscure importance. No holdout-driven feature selection.

Coefficients/tree importances may be added later with transformed-feature mapping; they do not replace the specified method. SHAP is optional future work.

## 8. K-Means lab — separate unsupervised protocol

- Numeric features only, no target. At least 30 rows and two usable numeric columns. Exclude all-missing and constant columns with an explicit message; reject if fewer than two remain.
- Pipeline: median imputer → StandardScaler → KMeans. Fit to the selected exploratory dataset; **no supervised holdout or accuracy metric** is claimed.
- Require `2 <= k <= min(10, n_unique_transformed_rows - 1, n_rows - 1)`. Record collapsed-cluster warnings. Cluster labels are identifiers without ordinal meaning.
- Elbow sweep uses k=1 through allowed maximum and records inertia. Silhouette is reported only for valid label counts, with a fixed sample of at most 2,000 rows; if that sample lacks enough distinct labels, return null/reason.
- Compute silhouette on the scaled modeling feature space. PCA may project to two dimensions for display only; do not score the 2D picture or imply that it preserves every distance.
- Persist config, preprocessing, model, cluster sizes, inertia, silhouette metadata and run seed. Compare only identical data/features/scaling with differing k.
- Store one selected-k K-Means trial per experiment. The elbow sweep is a diagnostic artifact with per-k values, not duplicate `kmeans` trial rows. Selection of k is exploratory and user-confirmed; there is no guaranteed optimal k.
- Predictions for new numeric rows are nearest-centroid assignments from the saved pipeline, not class labels or probability estimates.

Silhouette's validity conditions follow the [official API documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html).

## 9. Educational playground

Generate small 2D moons/blobs and a 1D noisy regression curve with recorded seed. Expose tree depth, kNN k, cluster k, noise and sample count (100–1,000). Plot actual fitted boundaries/curves; decision mesh <=200×200. Apply changes on an explicit Run button. Keep playground scores labeled as demonstration results, outside the formal experiment leaderboard. Each view explains what changed, what the algorithm assumes, and one limitation.
