"""Measure final offline performance goals and generate a real report artifact."""

from __future__ import annotations

import json
import platform
import time
import tracemalloc
import uuid

from datamind.config import get_settings
from datamind.contracts import AlgorithmConfig, DemoDatasetKind, TaskType
from datamind.services.datasets import DatasetService
from datamind.services.experiments import ExperimentService
from datamind.services.export import ExportService
from datamind.services.projects import ProjectService
from datamind.storage.database import run_migrations


def measure(callable_):
    tracemalloc.start()
    started = time.perf_counter()
    result = callable_()
    elapsed = time.perf_counter() - started
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak / (1024 * 1024)


def main() -> None:
    settings = get_settings()
    settings.ensure_directories()
    run_migrations(settings.db_path)
    project = ProjectService().create_project(f"M6 Evidence {uuid.uuid4().hex[:8]}")
    dataset_service = DatasetService()
    dataset, profile_seconds, profile_peak_mib = measure(
        lambda: dataset_service.load_demo(project.id, DemoDatasetKind.IRIS, seed=42)
    )
    service = ExperimentService(dataset_service=dataset_service)
    view = service.prepare_modeling_view(
        dataset.id,
        TaskType.CLASSIFICATION,
        "species",
        ["sepal_length", "sepal_width", "petal_length", "petal_width"],
        [],
    )
    manifest = service.prepare_split(dataset.id, view, random_seed=42)
    algorithms = [
        AlgorithmConfig(algorithm_id="logistic_regression"),
        AlgorithmConfig(algorithm_id="decision_tree_classifier"),
        AlgorithmConfig(algorithm_id="random_forest_classifier"),
    ]
    experiment, training_seconds, training_peak_mib = measure(
        lambda: service.run_supervised_experiment(
            "M6 Iris three-model evidence",
            project.id,
            dataset.id,
            view,
            manifest,
            algorithms,
            seed=42,
        )
    )
    evaluation = service.finalize_experiment(experiment.id)
    report = ExportService(dataset_service, service).generate_html_report(experiment.id)
    selected = next(
        trial for trial in experiment.trials if trial.trial_id == experiment.selected_trial_id
    )
    baseline = next(trial for trial in experiment.trials if trial.is_baseline)
    holdout_primary = next(
        metric for metric in evaluation.metrics if metric.name == experiment.primary_metric
    )
    evidence = {
        "hardware": {
            "platform": platform.platform(),
            "processor": platform.processor() or "not reported by platform module",
            "logical_cpu_count": __import__("os").cpu_count(),
        },
        "fixture": {"dataset": "Iris", "rows": dataset.row_count, "seed": 42},
        "profile": {"elapsed_seconds": profile_seconds, "peak_tracemalloc_mib": profile_peak_mib},
        "training": {
            "elapsed_seconds": training_seconds,
            "peak_tracemalloc_mib": training_peak_mib,
            "algorithms_plus_baseline": len(experiment.trials),
        },
        "result": {
            "experiment_id": experiment.id,
            "selected_algorithm": selected.algorithm_id,
            "cv_primary_mean": selected.primary_cv_mean,
            "cv_primary_std": selected.primary_cv_std,
            "baseline_cv_primary_mean": baseline.primary_cv_mean,
            "holdout_primary": holdout_primary.value,
            "holdout_previously_exposed": evaluation.holdout_previously_exposed,
        },
        "downloaded_report_example": str(report.resolve()),
    }
    evidence_path = settings.exports_dir / "m6_final_evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
