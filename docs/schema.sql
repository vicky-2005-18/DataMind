-- DataMind v1 baseline schema specification. Apply via numbered migration 001.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  archived_at TEXT
);

CREATE TABLE IF NOT EXISTS datasets (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id),
  display_name TEXT NOT NULL,
  source_kind TEXT NOT NULL CHECK(source_kind IN ('upload','demo')),
  source_json TEXT NOT NULL,
  raw_sha256 TEXT NOT NULL,
  raw_relative_path TEXT NOT NULL UNIQUE,
  parser_version TEXT NOT NULL,
  parser_config_json TEXT NOT NULL,
  schema_json TEXT NOT NULL,
  profile_json TEXT NOT NULL,
  row_count INTEGER NOT NULL CHECK(row_count > 0),
  column_count INTEGER NOT NULL CHECK(column_count > 0),
  created_at TEXT NOT NULL,
  archived_at TEXT
);

CREATE TABLE IF NOT EXISTS splits (
  id TEXT PRIMARY KEY,
  dataset_id TEXT NOT NULL REFERENCES datasets(id),
  task TEXT NOT NULL CHECK(task IN ('classification','regression')),
  target TEXT NOT NULL,
  view_fingerprint TEXT NOT NULL,
  split_fingerprint TEXT NOT NULL UNIQUE,
  config_json TEXT NOT NULL,
  row_policy_json TEXT NOT NULL,
  manifest_relative_path TEXT NOT NULL UNIQUE,
  manifest_sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiments (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id),
  dataset_id TEXT NOT NULL REFERENCES datasets(id),
  split_id TEXT REFERENCES splits(id),
  task TEXT NOT NULL CHECK(task IN ('classification','regression','clustering')),
  name TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('running','completed','failed','interrupted')),
  submission_token TEXT NOT NULL UNIQUE,
  config_json TEXT NOT NULL,
  config_sha256 TEXT NOT NULL,
  comparison_key TEXT NOT NULL,
  environment_json TEXT NOT NULL,
  registry_version TEXT NOT NULL,
  metric_version TEXT NOT NULL,
  random_seed INTEGER NOT NULL,
  primary_metric TEXT NOT NULL,
  retry_of_id TEXT REFERENCES experiments(id),
  started_at TEXT NOT NULL,
  finished_at TEXT,
  error_json TEXT,
  CHECK((task = 'clustering' AND split_id IS NULL) OR
        (task IN ('classification','regression') AND split_id IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS trials (
  id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL REFERENCES experiments(id),
  algorithm_id TEXT NOT NULL,
  is_baseline INTEGER NOT NULL DEFAULT 0 CHECK(is_baseline IN (0,1)),
  parameters_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('running','completed','failed','interrupted')),
  fit_duration_seconds REAL,
  warnings_json TEXT NOT NULL DEFAULT '[]',
  error_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(experiment_id, algorithm_id)
);

CREATE TABLE IF NOT EXISTS artifacts (
  id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL REFERENCES experiments(id),
  trial_id TEXT REFERENCES trials(id),
  kind TEXT NOT NULL,
  relative_path TEXT NOT NULL UNIQUE,
  sha256 TEXT NOT NULL,
  size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_selections (
  experiment_id TEXT PRIMARY KEY REFERENCES experiments(id),
  trial_id TEXT NOT NULL REFERENCES trials(id),
  selection_reason TEXT NOT NULL,
  selected_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluations (
  id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL REFERENCES experiments(id),
  trial_id TEXT NOT NULL REFERENCES trials(id),
  split_id TEXT NOT NULL REFERENCES splits(id),
  scope TEXT NOT NULL CHECK(scope = 'holdout'),
  holdout_previously_exposed INTEGER NOT NULL CHECK(holdout_previously_exposed IN (0,1)),
  created_at TEXT NOT NULL,
  UNIQUE(experiment_id, scope)
);

CREATE TABLE IF NOT EXISTS metrics (
  id TEXT PRIMARY KEY,
  trial_id TEXT NOT NULL REFERENCES trials(id),
  evaluation_id TEXT REFERENCES evaluations(id),
  name TEXT NOT NULL,
  scope TEXT NOT NULL CHECK(scope IN ('cv_fold','cv_mean','development','holdout','clustering')),
  fold_index INTEGER NOT NULL DEFAULT -1,
  value REAL,
  direction TEXT NOT NULL CHECK(direction IN ('maximize','minimize')),
  reason TEXT,
  details_json TEXT NOT NULL DEFAULT '{}',
  CHECK(value IS NOT NULL OR reason IS NOT NULL),
  CHECK((scope = 'holdout' AND evaluation_id IS NOT NULL) OR
        (scope <> 'holdout' AND evaluation_id IS NULL)),
  CHECK((scope = 'cv_fold' AND fold_index >= 0) OR
        (scope <> 'cv_fold' AND fold_index = -1))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_metric_key
ON metrics(trial_id, scope, name, fold_index, IFNULL(evaluation_id, ''));
CREATE INDEX IF NOT EXISTS ix_datasets_project ON datasets(project_id, created_at);
CREATE INDEX IF NOT EXISTS ix_experiments_history ON experiments(project_id, started_at);
CREATE INDEX IF NOT EXISTS ix_experiments_comparison ON experiments(comparison_key);
CREATE INDEX IF NOT EXISTS ix_trials_experiment ON trials(experiment_id);
CREATE INDEX IF NOT EXISTS ix_evaluations_split ON evaluations(split_id);
