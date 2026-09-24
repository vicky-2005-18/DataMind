"""Typed data contracts, DTOs, and error structures for DataMind."""

from __future__ import annotations

import warnings
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

warnings.filterwarnings(
    "ignore",
    message='Field name "schema_json" in "DatasetSummary" shadows an attribute in parent "BaseModel"',
    category=UserWarning,
)


class ErrorCode(str, Enum):
    """Standardized error codes defined in DATA_CONTRACTS."""

    INVALID_CSV = "INVALID_CSV"
    DATASET_LIMIT_EXCEEDED = "DATASET_LIMIT_EXCEEDED"
    INVALID_TARGET = "INVALID_TARGET"
    CONFLICTING_DUPLICATES = "CONFLICTING_DUPLICATES"
    UNSUPPORTED_FEATURE = "UNSUPPORTED_FEATURE"
    INSUFFICIENT_CLASS_SUPPORT = "INSUFFICIENT_CLASS_SUPPORT"
    TRANSFORM_LIMIT_EXCEEDED = "TRANSFORM_LIMIT_EXCEEDED"
    INVALID_MODEL_CONFIG = "INVALID_MODEL_CONFIG"
    WORKSPACE_BUSY = "WORKSPACE_BUSY"
    TRAINING_FAILED = "TRAINING_FAILED"
    PREDICTION_SCHEMA_MISMATCH = "PREDICTION_SCHEMA_MISMATCH"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    INCOMPATIBLE_COMPARISON = "INCOMPATIBLE_COMPARISON"
    METRIC_UNDEFINED = "METRIC_UNDEFINED"
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    PROJECT_ALREADY_EXISTS = "PROJECT_ALREADY_EXISTS"
    DATASET_NOT_FOUND = "DATASET_NOT_FOUND"


class ServiceError(Exception):
    """Application service error with structured metadata and user instructions."""

    def __init__(
        self,
        code: ErrorCode,
        user_message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
    ):
        super().__init__(user_message)
        self.code = code
        self.user_message = user_message
        self.field = field
        self.details = details or {}
        self.retryable = retryable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code.value,
            "user_message": self.user_message,
            "field": self.field,
            "details": self.details,
            "retryable": self.retryable,
        }


class ProjectSummary(BaseModel):
    """Data transfer object for local project summaries."""

    id: str
    name: str
    description: str = ""
    created_at: str
    archived_at: Optional[str] = None


class ProjectCreateRequest(BaseModel):
    """Input contract for creating a local project."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class ColumnRole(str, Enum):
    """Suggested semantic feature roles."""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    ID_LIKE = "id_like"
    CONSTANT = "constant"
    UNSUPPORTED = "unsupported"


class ColumnProfile(BaseModel):
    """Structural profile and statistics for an individual table column."""

    name: str
    dtype: str
    suggested_role: ColumnRole
    total_count: int
    non_null_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    is_constant: bool
    sample_values: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class DatasetProfile(BaseModel):
    """Complete structural profile of a validated dataset."""

    row_count: int
    column_count: int
    duplicate_row_count: int
    memory_bytes: int
    columns: List[ColumnProfile]
    quality_warnings: List[str] = Field(default_factory=list)


class ColumnSchema(BaseModel):
    """Schema descriptor for a dataset column."""

    name: str
    inferred_type: str
    suggested_role: ColumnRole


class TableSchema(BaseModel):
    """Overall schema definition for a tabular dataset."""

    columns: List[ColumnSchema]
    column_names: List[str]


class DemoDatasetKind(str, Enum):
    """Available offline demo datasets."""

    IRIS = "iris"
    SYNTHETIC_REGRESSION = "synthetic_regression"
    SYNTHETIC_BLOBS = "synthetic_blobs"


class DatasetSummary(BaseModel):
    """Persistent dataset metadata record matching SQLite schema."""

    model_config = ConfigDict(protected_namespaces=())

    id: str
    project_id: str
    display_name: str
    source_kind: str
    source_json: str
    raw_sha256: str
    raw_relative_path: str
    parser_version: str
    parser_config_json: str
    schema_json: str
    profile_json: str
    row_count: int
    column_count: int
    created_at: str
    archived_at: Optional[str] = None

    def get_profile(self) -> DatasetProfile:
        return DatasetProfile.model_validate_json(self.profile_json)

    def get_schema(self) -> TableSchema:
        return TableSchema.model_validate_json(self.schema_json)


class TaskType(str, Enum):
    """Supported machine learning task types."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"


class RowPolicy(BaseModel):
    """Policies governing row filtering and duplicate resolution."""

    drop_missing_target: bool = False
    drop_exact_duplicates: bool = False


class ModelingView(BaseModel):
    """Immutable view of dataset rows and feature roles for modeling."""

    dataset_id: str
    task: TaskType
    target: str
    numeric_features: List[str]
    categorical_features: List[str]
    eligible_row_ids: List[int]
    view_fingerprint: str
    row_policy: RowPolicy
    cleaning_log: List[str] = Field(default_factory=list)


class FoldIndices(BaseModel):
    """Explicit train and validation source row IDs for one CV fold."""

    fold_index: int
    train_row_ids: List[int]
    val_row_ids: List[int]


class SplitManifest(BaseModel):
    """Persistent manifest specifying exact train, holdout, and CV fold memberships."""

    split_id: str
    dataset_id: str
    view_fingerprint: str
    split_fingerprint: str
    task: TaskType
    target: str
    test_fraction: float
    cv_folds: int
    random_seed: int
    train_row_ids: List[int]
    test_row_ids: List[int]
    folds: List[FoldIndices]
    manifest_relative_path: str


class PreprocessingConfig(BaseModel):
    """Configuration for data transformers inside pipelines."""

    numeric_imputer: str = "median"  # median or mean
    numeric_scaler: str = "standard"  # standard, minmax, or passthrough
    categorical_imputer: str = "missing"  # missing


class AlgorithmConfig(BaseModel):
    """Specification of an algorithm and its hyperparameters."""

    algorithm_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class MetricScope(str, Enum):
    """Scope of a measured metric."""

    CV_FOLD = "cv_fold"
    CV_MEAN = "cv_mean"
    DEVELOPMENT = "development"
    HOLDOUT = "holdout"
    CLUSTERING = "clustering"


class MetricDirection(str, Enum):
    """Optimization direction for a metric."""

    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


class MetricRecord(BaseModel):
    """Individual metric measurement matching the metrics table."""

    id: str
    trial_id: str
    evaluation_id: Optional[str] = None
    name: str
    scope: MetricScope
    fold_index: int = -1
    value: Optional[float] = None
    direction: MetricDirection
    reason: Optional[str] = None
    details_json: str = "{}"


class TrialResult(BaseModel):
    """Execution result for a single algorithm trial."""

    trial_id: str
    experiment_id: str
    algorithm_id: str
    is_baseline: bool
    parameters: Dict[str, Any]
    status: str
    fit_duration_seconds: float
    warnings: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    metrics: List[MetricRecord] = Field(default_factory=list)
    primary_cv_mean: Optional[float] = None
    primary_cv_std: Optional[float] = None


class ExperimentSummary(BaseModel):
    """Persisted experiment summary."""

    id: str
    project_id: str
    dataset_id: str
    split_id: Optional[str]
    task: TaskType
    name: str
    status: str
    submission_token: str
    config_json: str
    comparison_key: str
    random_seed: int
    primary_metric: str
    started_at: str
    finished_at: Optional[str] = None
    trials: List[TrialResult] = Field(default_factory=list)
    selected_trial_id: Optional[str] = None
    selection_reason: Optional[str] = None


class HoldoutEvaluation(BaseModel):
    """Immutable holdout evaluation record."""

    id: str
    experiment_id: str
    trial_id: str
    split_id: str
    scope: str = "holdout"
    holdout_previously_exposed: bool
    created_at: str
    metrics: List[MetricRecord] = Field(default_factory=list)
    confusion_matrix: Optional[List[List[int]]] = None
    class_labels: Optional[List[str]] = None


class PredictionBatch(BaseModel):
    """Output batch of predictions with optional class probabilities and warnings."""

    row_ids: List[int]
    predictions: List[Any]
    probabilities: Optional[List[List[float]]] = None
    classes: Optional[List[str]] = None
    warnings: List[str] = Field(default_factory=list)


class ClusteringResult(BaseModel):
    """Persisted K-Means result and diagnostic artifact references."""

    experiment: ExperimentSummary
    feature_names: List[str]
    cluster_labels: List[int]
    cluster_sizes: Dict[int, int]
    inertia: float
    silhouette: Optional[float] = None
    silhouette_reason: Optional[str] = None
    silhouette_sample_size: int
    pca_coordinates: List[List[float]]
    pca_explained_variance: List[float]
    elbow_points: List[Dict[str, float]]
    artifact_paths: Dict[str, str]
    warnings: List[str] = Field(default_factory=list)


class PlaygroundResult(BaseModel):
    """Real fitted output for an educational synthetic playground."""

    kind: str
    seed: int
    parameters: Dict[str, Any]
    points: List[List[float]]
    labels: List[Any]
    mesh_x: Optional[List[List[float]]] = None
    mesh_y: Optional[List[List[float]]] = None
    mesh_values: Optional[List[List[float]]] = None
    curve_x: Optional[List[float]] = None
    curve_y: Optional[List[float]] = None
    explanation: str
    limitation: str


class ComparisonResult(BaseModel):
    """Outcome of comparing multiple experiments for leaderboard compatibility."""

    is_compatible: bool
    primary_metric: str
    candidate_experiment_ids: List[str]
    table_rows: List[Dict[str, Any]] = Field(default_factory=list)
    mismatch_reasons: List[str] = Field(default_factory=list)
    config_differences: List[Dict[str, Any]] = Field(default_factory=list)


class InputFeatureSchema(BaseModel):
    """Saved schema expected by a fitted model at inference time."""

    feature_names: List[str]
    numeric_features: List[str]
    categorical_features: List[str]
    expected_dtypes: Dict[str, str] = Field(default_factory=dict)


class PermutationImportanceRecord(BaseModel):
    """Bounded permutation importance record for one original input feature.

    Values represent the mean decrease in primary CV metric when the feature
    is permuted. Computed on development rows only as a diagnostic.
    """

    feature: str
    mean_importance: float
    std_importance: float
    n_repeats: int
    n_samples: int


class ExportManifest(BaseModel):
    """Manifest of files in a ZIP bundle with checksums and origins."""

    experiment_id: str
    generated_at: str
    files: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    raw_training_data_included: bool = False


class ExperimentReportConfig(BaseModel):
    """Configuration for generating experiment reports."""

    include_permutation_importance: bool = True
    include_holdout_evaluation: bool = True
    include_cv_details: bool = True
    include_environment: bool = True
    include_failures: bool = True
    include_exposure_flags: bool = True
    include_artifact_hashes: bool = True
    include_raw_training_data: bool = False  # Excluded by default per DATA_CONTRACTS
