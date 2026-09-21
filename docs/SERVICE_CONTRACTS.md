# Internal service contracts

These are Python interfaces, not REST endpoints. Data classes/Pydantic models live in `datamind/contracts.py`. UI passes typed inputs and renders typed outputs; it never reaches directly into database internals.

| Interface | Input | Output and important behavior |
|---|---|---|
| `ProjectService.create_project` | name, description | ProjectSummary with generated ID |
| `DatasetService.import_csv` | project_id, bytes, display_name, parser config | DatasetSummary; persists immutable source after validation |
| `DatasetService.load_demo` | project_id, demo_id, seed | Same DatasetSummary contract; no network |
| `DatasetService.profile` | dataset_id | DatasetProfile; structural metadata |
| `ExperimentService.prepare_view` | dataset_id, task, target, roles, row policy | ModelingView with eligible source IDs and warnings |
| `ExperimentService.prepare_split` | ModelingView, split config | SplitSummary; creates/reuses exact manifest |
| `ExplorationService.summarize` | dataset_id, split_id, chart config | DevelopmentDataSummary plus deterministic sampled charts |
| `ExperimentService.run` | ExperimentConfig, submission_token | ExperimentSummary; lock, validate, train, persist |
| `ExperimentService.finalize` | experiment_id | HoldoutEvaluation; idempotent and immutable |
| `ExperimentService.clone_config` | experiment_id | Draft config only; no immediate training |
| `ComparisonService.compare` | experiment_ids | ComparableResult or mismatched field errors |
| `PredictionService.predict` | trial_id, rows, extra-column policy | Predictions, original row order, warning counts |
| `ExplanationService.permutation` | trial_id, bounded config | Labeled development diagnostic and sampling metadata |
| `ClusteringService.run` | ClusteringConfig, submission_token | Stored unsupervised ExperimentSummary |
| `ReportService.export` | experiment_id, requested formats | Registered export artifacts with manifest |
| `RecoveryService.reconcile` | storage root | Counts of interrupted rows / missing artifacts, under lock |

## Suggested typed objects

- `DatasetProfile`: counts, inferred/confirmed roles, missing counts, duplicates, constants, parsing warnings.
- `ModelingView`: dataset_id, source row mapping, task, target, ordered features, view_fingerprint, cleaning log.
- `SplitManifest`: schema_version, split_id, view_fingerprint, train_row_ids, test_row_ids, folds containing train/validation source row IDs, seed, split_fingerprint.
- `ExperimentConfig`: union of SupervisedConfig and ClusteringConfig, discriminated by task.
- `TrialResult`: algorithm, resolved parameters, fold scores, aggregate metrics, status, warnings, timings, optional model handle.
- `ExperimentSummary`: ID, state, completed/failed trials, selected_trial_id, optional evaluation, warnings.
- `PredictionBatch`: row IDs, predictions, optional class probabilities, class order, warnings.
- `ExportManifest`: schema_version, experiment_id, artifacts with relative filenames and SHA-256, environment, data inclusion policy.

## Error boundary

ML helpers raise typed domain errors or controlled exceptions. Service layer converts them to the `ServiceError` contract, records failure when an experiment exists, and releases locks in `finally`. UI displays a short message and corrective step. Preserve full traceback in local diagnostic logs without dataset values. Do not use a broad catch that returns a successful empty result.

## Rerun and submission contract

The form creates a submission token once per intentional submit. Store its ID before invoking `run`. If the same token is retried, return the existing experiment; if still running, show its state. Changing settings invalidates the draft token. Running again intentionally creates a new token. The database uniqueness constraint is the final guard, not just a disabled button.

## Implementation order

Typed config + repository initialization → demo ingestion → pure split/pipeline/metric functions → run orchestration → UI integration → prediction/export. This lets tests exercise the ML workflow without launching the browser.
