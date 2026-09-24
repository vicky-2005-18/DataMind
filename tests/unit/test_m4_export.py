"""M4 explanation, evidence export, and safe CSV verification."""

from __future__ import annotations

import hashlib
import html
import json
import tempfile
import uuid
import zipfile
from pathlib import Path

import joblib
import pandas as pd
import pytest

from datamind.config import get_settings
from datamind.contracts import AlgorithmConfig, DemoDatasetKind, PredictionBatch, TaskType
from datamind.ml.experiment import compute_permutation_importance
from datamind.services.datasets import DatasetService
from datamind.services.experiments import ExperimentService
from datamind.services.export import ExportService
from datamind.services.prediction import PredictionService
from datamind.services.projects import ProjectService


@pytest.fixture
def iris_experiment(migrated_db):
    project = ProjectService().create_project(f"M4 <script>{uuid.uuid4().hex[:8]}</script>")
    dataset_service = DatasetService()
    dataset = dataset_service.load_demo(project.id, DemoDatasetKind.IRIS)
    experiment_service = ExperimentService(dataset_service=dataset_service)
    view = experiment_service.prepare_modeling_view(
        dataset.id,
        TaskType.CLASSIFICATION,
        "species",
        ["sepal_length", "sepal_width", "petal_length", "petal_width"],
        [],
    )
    manifest = experiment_service.prepare_split(dataset.id, view, random_seed=42)
    experiment = experiment_service.run_supervised_experiment(
        "Iris <b>evidence</b>",
        project.id,
        dataset.id,
        view,
        manifest,
        [AlgorithmConfig(algorithm_id="logistic_regression", parameters={"C": 1.0})],
        seed=42,
    )
    evaluation = experiment_service.finalize_experiment(experiment.id)
    return dataset_service, experiment_service, dataset, manifest, experiment, evaluation


def test_t32_permutation_diagnostic_is_deterministic_and_labeled(iris_experiment):
    dataset_service, _service, dataset, manifest, experiment, _evaluation = iris_experiment
    settings = get_settings()
    schema = json.loads(
        (settings.experiments_dir / experiment.id / "input_schema.json").read_text(encoding="utf-8")
    )
    pipeline = joblib.load(settings.experiments_dir / experiment.id / "champion.joblib")
    frame = dataset_service.load_dataframe(dataset.id)
    arguments = {
        "pipeline": pipeline,
        "X_dev": frame.loc[manifest.train_row_ids, schema["feature_names"]],
        "y_dev": frame.loc[manifest.train_row_ids, "species"],
        "feature_names": schema["feature_names"],
        "task": TaskType.CLASSIFICATION,
        "seed": 42,
    }
    first = compute_permutation_importance(**arguments)
    second = compute_permutation_importance(**arguments)
    assert first == second
    assert [record.feature for record in first] == schema["feature_names"]
    assert all(record.n_samples == len(manifest.train_row_ids) for record in first)

    report = ExportService(dataset_service, _service).generate_html_report(experiment.id).read_text(
        encoding="utf-8"
    )
    assert "development-set diagnostic" in report.lower()
    assert "not causal evidence" in report.lower()
    assert "sepal_length" in report


def test_t33_model_and_experiment_zip_records_and_checksums(iris_experiment):
    dataset_service, service, dataset, manifest, experiment, evaluation = iris_experiment
    exporter = ExportService(dataset_service, service)
    model_zip = exporter.create_model_zip(experiment.id)
    expected_model_files = {
        "pipeline.joblib",
        "input_schema.json",
        "experiment_config.json",
        "metrics.json",
        "environment.json",
        "README.md",
        "manifest.json",
    }
    with zipfile.ZipFile(model_zip) as archive:
        assert set(archive.namelist()) == expected_model_files
        manifest_data = json.loads(archive.read("manifest.json"))
        assert manifest_data["raw_training_data_included"] is False
        for name, details in manifest_data["files"].items():
            assert name in archive.namelist()
            assert hashlib.sha256(archive.read(name)).hexdigest() == details["sha256"]
            assert details["size_bytes"] == len(archive.read(name))
            assert Path(name).is_absolute() is False
            assert "origin" in details
        config = json.loads(archive.read("experiment_config.json"))
        assert config["target"] == "species"
        assert config["split_fingerprint"] == manifest.split_fingerprint
        metrics = json.loads(archive.read("metrics.json"))
        assert metrics["selected_trial_id"] == experiment.selected_trial_id
        assert metrics["holdout_evaluation"]["id"] == evaluation.id
        readme = archive.read("README.md").decode()
        assert "only when this trusted" in readme
        assert "compatible" in readme

    experiment_zip = exporter.create_experiment_zip(experiment.id)
    with zipfile.ZipFile(experiment_zip) as archive:
        assert "raw.csv" not in " ".join(archive.namelist())
        assert "report.html" in archive.namelist()
        assert "report.md" in archive.namelist()
        manifest_data = json.loads(archive.read("manifest.json"))
        for name, details in manifest_data["files"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == details["sha256"]


def test_t34_html_and_safe_csv_export(iris_experiment):
    dataset_service, service, _dataset, _manifest, experiment, _evaluation = iris_experiment
    exporter = ExportService(dataset_service, service)
    html_report = exporter.generate_html_report(experiment.id).read_text(encoding="utf-8")
    assert "<b>evidence</b>" not in html_report
    assert html.escape("Iris <b>evidence</b>") in html_report

    input_frame = pd.DataFrame(
        {
            "text": ["=1+1", "+SUM(A1:A2)", "-2+3", "@cmd", "\tformula", "\rformula", "safe"],
            "number": [-4, 1, 2, 3, 4, 5, 6],
        }
    )
    batch = PredictionBatch(row_ids=list(range(7)), predictions=["ok"] * 7)
    csv_bytes = PredictionService().export_batch_csv(input_frame, batch, "label")
    parsed = pd.read_csv(pd.io.common.BytesIO(csv_bytes), keep_default_na=False)
    assert parsed["text"].tolist()[:6] == [
        "'=1+1",
        "'+SUM(A1:A2)",
        "'-2+3",
        "'@cmd",
        "'\tformula",
        "'\rformula",
    ]
    assert parsed["number"].tolist()[0] == -4


def test_model_export_reload_consistency(iris_experiment):
    dataset_service, service, dataset, _manifest, experiment, _evaluation = iris_experiment
    model_zip = ExportService(dataset_service, service).create_model_zip(experiment.id)
    frame = dataset_service.load_dataframe(dataset.id)
    with tempfile.TemporaryDirectory() as directory:
        with zipfile.ZipFile(model_zip) as archive:
            archive.extractall(directory)
        exported = joblib.load(Path(directory) / "pipeline.joblib")
        original = joblib.load(get_settings().experiments_dir / experiment.id / "champion.joblib")
        schema = json.loads((Path(directory) / "input_schema.json").read_text(encoding="utf-8"))
        sample = frame.loc[:10, schema["feature_names"]]
        assert (original.predict(sample) == exported.predict(sample)).all()
