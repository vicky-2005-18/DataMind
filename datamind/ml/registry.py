"""Model algorithm registry, hyperparameter validation, and estimator factories."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from sklearn.base import BaseEstimator
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from datamind.contracts import ErrorCode, ServiceError, TaskType


class AlgorithmDescriptor:
    """Descriptor defining supported algorithms, parameter boundaries, and complexity."""

    def __init__(
        self,
        algorithm_id: str,
        display_name: str,
        task: TaskType,
        is_baseline: bool,
        complexity_order: int,
        default_params: Dict[str, Any],
        factory_fn: Callable[[Dict[str, Any], int], BaseEstimator],
        param_validator: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.algorithm_id = algorithm_id
        self.display_name = display_name
        self.task = task
        self.is_baseline = is_baseline
        self.complexity_order = complexity_order
        self.default_params = default_params
        self.factory_fn = factory_fn
        self.param_validator = param_validator

    def build_estimator(self, params: Dict[str, Any], seed: int) -> BaseEstimator:
        merged = {**self.default_params, **params}
        if self.param_validator:
            self.param_validator(merged)
        return self.factory_fn(merged, seed)


def _validate_logistic_params(params: Dict[str, Any]) -> None:
    c_val = float(params.get("C", 1.0))
    if c_val <= 0:
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "Parameter 'C' must be positive.")


def _validate_tree_params(params: Dict[str, Any]) -> None:
    depth = params.get("max_depth", 5)
    if depth is not None and not (1 <= int(depth) <= 20):
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "max_depth must be between 1 and 20.")
    leaf = int(params.get("min_samples_leaf", 1))
    if leaf < 1 or leaf > 20:
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "min_samples_leaf must be between 1 and 20.")


def _validate_forest_params(params: Dict[str, Any]) -> None:
    trees = int(params.get("n_estimators", 100))
    if not (50 <= trees <= 200):
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "n_estimators must be between 50 and 200.")
    depth = params.get("max_depth", 10)
    if depth is not None and not (2 <= int(depth) <= 20):
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "max_depth must be between 2 and 20.")


def _validate_knn_params(params: Dict[str, Any]) -> None:
    k = int(params.get("n_neighbors", 5))
    if not (1 <= k <= 25):
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "n_neighbors must be between 1 and 25.")
    weights = params.get("weights", "uniform")
    if weights not in ("uniform", "distance"):
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "weights must be 'uniform' or 'distance'.")


def _validate_ridge_params(params: Dict[str, Any]) -> None:
    alpha = float(params.get("alpha", 1.0))
    if alpha <= 0:
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "Parameter 'alpha' must be positive.")


REGISTRY: Dict[str, AlgorithmDescriptor] = {
    # Classification
    "dummy_classifier": AlgorithmDescriptor(
        algorithm_id="dummy_classifier",
        display_name="Baseline (Most Frequent Class)",
        task=TaskType.CLASSIFICATION,
        is_baseline=True,
        complexity_order=0,
        default_params={"strategy": "most_frequent"},
        factory_fn=lambda p, s: DummyClassifier(strategy=p["strategy"]),
    ),
    "logistic_regression": AlgorithmDescriptor(
        algorithm_id="logistic_regression",
        display_name="Logistic Regression",
        task=TaskType.CLASSIFICATION,
        is_baseline=False,
        complexity_order=1,
        default_params={"C": 1.0, "max_iter": 1000},
        factory_fn=lambda p, s: LogisticRegression(C=float(p["C"]), max_iter=int(p["max_iter"]), random_state=s),
        param_validator=_validate_logistic_params,
    ),
    "decision_tree_classifier": AlgorithmDescriptor(
        algorithm_id="decision_tree_classifier",
        display_name="Decision Tree Classifier",
        task=TaskType.CLASSIFICATION,
        is_baseline=False,
        complexity_order=2,
        default_params={"max_depth": 5, "min_samples_leaf": 1},
        factory_fn=lambda p, s: DecisionTreeClassifier(
            max_depth=int(p["max_depth"]) if p["max_depth"] else None,
            min_samples_leaf=int(p["min_samples_leaf"]),
            random_state=s,
        ),
        param_validator=_validate_tree_params,
    ),
    "random_forest_classifier": AlgorithmDescriptor(
        algorithm_id="random_forest_classifier",
        display_name="Random Forest Classifier",
        task=TaskType.CLASSIFICATION,
        is_baseline=False,
        complexity_order=4,
        default_params={"n_estimators": 100, "max_depth": 10},
        factory_fn=lambda p, s: RandomForestClassifier(
            n_estimators=int(p["n_estimators"]),
            max_depth=int(p["max_depth"]) if p["max_depth"] else None,
            n_jobs=1,
            random_state=s,
        ),
        param_validator=_validate_forest_params,
    ),
    "knn_classifier": AlgorithmDescriptor(
        algorithm_id="knn_classifier",
        display_name="k-Nearest Neighbors (kNN)",
        task=TaskType.CLASSIFICATION,
        is_baseline=False,
        complexity_order=3,
        default_params={"n_neighbors": 5, "weights": "uniform"},
        factory_fn=lambda p, s: KNeighborsClassifier(
            n_neighbors=int(p["n_neighbors"]),
            weights=p["weights"],
            n_jobs=1,
        ),
        param_validator=_validate_knn_params,
    ),
    # Regression
    "dummy_regressor": AlgorithmDescriptor(
        algorithm_id="dummy_regressor",
        display_name="Baseline (Mean Target)",
        task=TaskType.REGRESSION,
        is_baseline=True,
        complexity_order=0,
        default_params={"strategy": "mean"},
        factory_fn=lambda p, s: DummyRegressor(strategy=p["strategy"]),
    ),
    "linear_regression": AlgorithmDescriptor(
        algorithm_id="linear_regression",
        display_name="Linear Regression (OLS)",
        task=TaskType.REGRESSION,
        is_baseline=False,
        complexity_order=1,
        default_params={},
        factory_fn=lambda p, s: LinearRegression(n_jobs=1),
    ),
    "ridge": AlgorithmDescriptor(
        algorithm_id="ridge",
        display_name="Ridge Regression (L2 Regularized)",
        task=TaskType.REGRESSION,
        is_baseline=False,
        complexity_order=1,
        default_params={"alpha": 1.0},
        factory_fn=lambda p, s: Ridge(alpha=float(p["alpha"]), random_state=s),
        param_validator=_validate_ridge_params,
    ),
    "decision_tree_regressor": AlgorithmDescriptor(
        algorithm_id="decision_tree_regressor",
        display_name="Decision Tree Regressor",
        task=TaskType.REGRESSION,
        is_baseline=False,
        complexity_order=2,
        default_params={"max_depth": 5, "min_samples_leaf": 1},
        factory_fn=lambda p, s: DecisionTreeRegressor(
            max_depth=int(p["max_depth"]) if p["max_depth"] else None,
            min_samples_leaf=int(p["min_samples_leaf"]),
            random_state=s,
        ),
        param_validator=_validate_tree_params,
    ),
    "random_forest_regressor": AlgorithmDescriptor(
        algorithm_id="random_forest_regressor",
        display_name="Random Forest Regressor",
        task=TaskType.REGRESSION,
        is_baseline=False,
        complexity_order=4,
        default_params={"n_estimators": 100, "max_depth": 10},
        factory_fn=lambda p, s: RandomForestRegressor(
            n_estimators=int(p["n_estimators"]),
            max_depth=int(p["max_depth"]) if p["max_depth"] else None,
            n_jobs=1,
            random_state=s,
        ),
        param_validator=_validate_forest_params,
    ),
}


def get_algorithms_for_task(task: TaskType) -> List[AlgorithmDescriptor]:
    """Return all allowlisted algorithm descriptors for a specific task."""
    return [desc for desc in REGISTRY.values() if desc.task == task]


def get_baseline_for_task(task: TaskType) -> AlgorithmDescriptor:
    """Get the mandatory baseline algorithm descriptor for a task."""
    baselines = [desc for desc in REGISTRY.values() if desc.task == task and desc.is_baseline]
    if not baselines:
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, f"No baseline defined for task {task}.")
    return baselines[0]


def get_algorithm(algorithm_id: str) -> AlgorithmDescriptor:
    """Retrieve an algorithm descriptor by ID or raise INVALID_MODEL_CONFIG."""
    if algorithm_id not in REGISTRY:
        raise ServiceError(
            ErrorCode.INVALID_MODEL_CONFIG,
            f"Algorithm '{algorithm_id}' is not in the allowlisted algorithm registry.",
            field=algorithm_id,
        )
    return REGISTRY[algorithm_id]
