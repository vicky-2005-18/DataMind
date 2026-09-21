# Data, configuration and error contracts

## Supported input

UTF-8 or UTF-8-BOM CSV, comma delimiter, one header row. UTF-8-BOM must be decoded with `utf-8-sig`. Other encodings, Excel, compressed archives, remote URLs, JSON, images and arbitrary code are outside v1 upload scope. File extension is only an initial check; parse and validate actual bytes. The app receives file bytes, not a user-selected server path.

## Hard product limits

| Setting | Default / maximum | Enforcement |
|---|---|---|
| Upload size | 10 MiB = 10×1024×1024 bytes | Before parse; align Streamlit uploader limit |
| Training table | 20,000 rows, 100 raw columns | Read at most row limit+1; reject excess |
| Cell string length | 1,000 characters | Reject overly large text cells |
| Categorical feature | At most 50 nonmissing distinct values | Over-limit field must be excluded or explicitly recast; no silent truncation |
| Transformed matrix | 500 columns, 10,000,000 cells | Conservative bound before materialization, check actual after fitting |
| Supervised experiment | 4 nonbaseline models + baseline | Registry and request validation |
| CV | 3 or 5 folds | Split feasibility validated |
| Predictions | 5,000 rows per batch | Same byte/column validation as training upload |
| EDA scatter | Seeded sample of at most 2,000 rows | Show sample count; profile counts use full relevant table |
| Plot correlation | Up to 30 selected numeric features | Require explicit selection above limit |
| Parallel fits | 1 | Workspace lock; model n_jobs=1 |

Limits are conservative implementation requirements, not performance guarantees. Do not silently subsample training rows to meet them.

## Validation sequence

1. Check byte limit and decode; reject empty data or headers-only data.
2. Inspect raw header before pandas can automatically rename duplicates. Trim header whitespace; reject empty/duplicate names after normalization. Preserve original-to-normalized mapping.
3. Parse with strict row-shape/error handling; reject malformed quoting, extra/missing fields and ambiguous delimiter. Blank physical lines may be ignored but must not create phantom records.
4. Assign stable zero-based source row IDs as metadata, not ML features. Reject over-limit rows, columns and string lengths.
5. Recognize missing values with a documented small list: blank fields and explicit `NaN`/`null` tokens. Do not silently treat category strings such as `NA` as missing. Record parser settings.
6. Numeric columns must contain finite values or missing values. Reject ±infinity with row/column location. Mixed types produce a suggested role plus user confirmation, not silent coercion that loses data.
7. Report constants, missingness, duplicate rows and high-cardinality/ID-like fields. Role defaults are suggestions; show exclusions before applying them.
8. Task-specific target and split validation follows ML_SPEC. Unsupported repeated-entity/time-series data is clearly outside supported evaluation.

Changing parser settings creates a new dataset version even if bytes match. A raw SHA-256 alone does not fully identify a parsed dataset.

## Configuration contract

Use Pydantic models, `extra='forbid'`, strict supported enums and versioned config. See `examples/` in the root. Unknown properties fail validation; defaults are explicit and stored after resolution. Example IDs are placeholders to replace after creating actual local records.

| Field | Meaning |
|---|---|
| schema_version | Integer contract version, initially 1 |
| project_id / dataset_id | Existing local record IDs |
| task | classification, regression or clustering |
| target | Required string for supervised; null for clustering |
| feature_roles | Separate numeric/categorical arrays; disjoint and existing columns |
| row_policy | Target-missing and exact-duplicate handling |
| preprocessing | Imputer/encoder/scaler choices |
| split | Supervised test fraction, CV folds and seed; null for clustering |
| models | Allowlisted algorithm IDs and bounded parameter dictionaries |
| primary_metric | f1_macro / rmse / silhouette as appropriate |
| random_seed | Nonnegative integer in supported estimator range |

Reject target in any feature list, overlapping roles, empty feature lists, duplicate algorithm entries and task/algorithm mismatch. Store canonical sorted-key JSON and SHA-256; preserve model ordering separately if necessary for user display.

## Prediction input and output

Input schema is saved at model fit time, not inferred afresh. Require every selected feature exactly once; align columns by name, then reorder to saved order. Unexpected columns cause an actionable error by default; offer an explicit exclude-extra-columns option. Target is not required and is treated as extra if supplied.

- Missing cell values are allowed if covered by the fitted imputer; missing columns are not.
- Numeric coercion must be explicit and validated; `age='abc'` is an error, not NaN.
- Unseen categorical values use encoder's saved unknown behavior and return a warning with counts. Never refit to learn the new values.
- Single-row and CSV-batch paths call the same prediction service.
- Output preserves input row order, adds prediction, and includes probabilities only when supported, using saved `classes_` order. Probabilities are model estimates, not confidence guarantees.
- Clustering outputs `cluster_id` with no classifier probability column.
- CSV downloads escape spreadsheet-formula prefixes in text cells (`=`, `+`, `-`, `@`, tab/CR), while preserving actual numeric cells as numbers. Test export roundtrip and escaping.

## Standard result shapes

`MetricValue`: name, value (finite float or null), direction (`maximize`/`minimize`), scope (`cv_fold`/`cv_mean`/`development`/`holdout`/`clustering`), optional fold_index, reason, details.

`ServiceError`: code, user_message, field (optional), details (non-sensitive dictionary), retryable (bool). Internally log trace ID and exception type; do not include full uploaded rows, API secrets or raw artifact paths in UI messages.

## Error codes

| Code | User-facing instruction |
|---|---|
| INVALID_CSV | Fix the indicated encoding/header/row shape and upload again |
| DATASET_LIMIT_EXCEEDED | Reduce file size/rows/columns to the stated limit |
| INVALID_TARGET | Choose a valid target or explicitly handle missing target rows |
| CONFLICTING_DUPLICATES | Resolve identical inputs with conflicting labels |
| UNSUPPORTED_FEATURE | Exclude/recast the named text, datetime or high-cardinality feature |
| INSUFFICIENT_CLASS_SUPPORT | Add class examples or choose an appropriate dataset |
| TRANSFORM_LIMIT_EXCEEDED | Reduce categorical features or selected columns |
| INVALID_MODEL_CONFIG | Fix the named parameter; show allowed values |
| WORKSPACE_BUSY | Another operation is running; return after it completes |
| TRAINING_FAILED | Keep the configuration and show the failed model reason |
| PREDICTION_SCHEMA_MISMATCH | Match the listed expected feature columns/types |
| MODEL_UNAVAILABLE | Model artifact is missing/incompatible; rerun training |
| INCOMPATIBLE_COMPARISON | Select experiments with matching comparison fields |
| METRIC_UNDEFINED | Explain the mathematical condition; display N/A |

## Exports

Model ZIP: `pipeline.joblib`, `input_schema.json`, `experiment_config.json`, `metrics.json`, `environment.json`, `manifest.json`, `README.md`. Manifest gives checksums and origins; no absolute paths. Export cannot be reimported through the UI in v1. Document that joblib must only be loaded from trusted sources and compatible environments. Report includes task, source, cleaning counts, split, CV, selected model, holdout exposure status, failures, limits and timestamps. Raw training data is excluded by default.
