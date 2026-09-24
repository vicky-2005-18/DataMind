"""Evidence report and model/experiment export service."""

from __future__ import annotations

import datetime
import hashlib
import html
import io
import json
import platform
import sys
import zipfile
from pathlib import Path
from typing import Any, Optional

import joblib

from datamind.config import get_settings
from datamind.contracts import ErrorCode, ExperimentSummary, ServiceError, TaskType
from datamind.ml.experiment import compute_permutation_importance
from datamind.services.datasets import DatasetService
from datamind.services.experiments import ExperimentService
from datamind.storage.artifacts import compute_sha256_file, write_atomic_bytes
from datamind.storage.database import get_connection


class ExportService:
    """Generate escaped reports and checksum-verified ZIP bundles from saved records."""

    def __init__(
        self,
        dataset_service: Optional[DatasetService] = None,
        experiment_service: Optional[ExperimentService] = None,
    ):
        self.dataset_service = dataset_service or DatasetService()
        self.experiment_service = experiment_service or ExperimentService(
            dataset_service=self.dataset_service
        )

    def _collect(self, experiment_id: str) -> dict[str, Any]:
        experiment = self.experiment_service.get_experiment(experiment_id)
        if experiment is None or experiment.task == TaskType.CLUSTERING:
            raise ServiceError(
                ErrorCode.INVALID_MODEL_CONFIG,
                "Evidence export requires a saved supervised experiment.",
            )
        dataset = self.dataset_service.get_dataset(experiment.dataset_id)
        if dataset is None:
            raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "Experiment dataset is unavailable.")
        config = json.loads(experiment.config_json)
        target = config.get("target")
        if not target:
            raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "Saved experiment target is missing.")
        manifest = self.experiment_service.split_repo.get_by_id(experiment.split_id)
        if manifest is None:
            raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "Saved split manifest is unavailable.")
        evaluation = self.experiment_service.get_evaluation(experiment_id)
        settings = get_settings()
        experiment_dir = settings.experiments_dir / experiment_id
        schema_path = experiment_dir / "input_schema.json"
        model_path = experiment_dir / "champion.joblib"
        if not model_path.exists() and experiment.selected_trial_id:
            model_path = experiment_dir / f"{experiment.selected_trial_id}_champion.joblib"
        if not schema_path.exists() or not model_path.exists():
            raise ServiceError(ErrorCode.MODEL_UNAVAILABLE, "Saved model or input schema is unavailable.")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        environment = self._load_environment(experiment_id)
        return {
            "experiment": experiment,
            "dataset": dataset,
            "config": config,
            "target": target,
            "manifest": manifest,
            "evaluation": evaluation,
            "experiment_dir": experiment_dir,
            "schema": schema,
            "schema_path": schema_path,
            "model_path": model_path,
            "environment": environment,
        }

    @staticmethod
    def _load_environment(experiment_id: str) -> dict[str, Any]:
        conn = get_connection(get_settings().db_path)
        try:
            row = conn.execute(
                "SELECT environment_json FROM experiments WHERE id = ?", (experiment_id,)
            ).fetchone()
        finally:
            conn.close()
        if row:
            return json.loads(row["environment_json"])
        return {"python": sys.version, "platform": platform.platform(), "packages": {}}

    def compute_importance(self, experiment_id: str) -> list[dict[str, Any]]:
        evidence = self._collect(experiment_id)
        frame = self.dataset_service.load_dataframe(evidence["experiment"].dataset_id)
        features = evidence["schema"]["feature_names"]
        development_ids = evidence["manifest"].train_row_ids
        pipeline = joblib.load(evidence["model_path"])
        records = compute_permutation_importance(
            pipeline=pipeline,
            X_dev=frame.loc[development_ids, features],
            y_dev=frame.loc[development_ids, evidence["target"]],
            feature_names=features,
            task=evidence["experiment"].task,
            seed=42,
            n_repeats=5,
            max_features=50,
            sample_rows=500,
        )
        return [record.model_dump() for record in records]

    @staticmethod
    def _metric_payload(experiment: ExperimentSummary, evaluation: Any) -> dict[str, Any]:
        return {
            "primary_metric": experiment.primary_metric,
            "selected_trial_id": experiment.selected_trial_id,
            "selection_reason": experiment.selection_reason,
            "trials": [trial.model_dump(mode="json") for trial in experiment.trials],
            "holdout_evaluation": evaluation.model_dump(mode="json") if evaluation else None,
        }

    def _report_payload(self, experiment_id: str) -> dict[str, Any]:
        evidence = self._collect(experiment_id)
        experiment = evidence["experiment"]
        dataset = evidence["dataset"]
        manifest = evidence["manifest"]
        selected = next(
            (trial for trial in experiment.trials if trial.trial_id == experiment.selected_trial_id),
            None,
        )
        importance = self.compute_importance(experiment_id)
        return {
            **evidence,
            "selected": selected,
            "importance": sorted(importance, key=lambda row: abs(row["mean_importance"]), reverse=True),
            "source": json.loads(dataset.source_json),
            "parser": json.loads(dataset.parser_config_json),
            "split": {
                "development_rows": len(manifest.train_row_ids),
                "holdout_rows": len(manifest.test_row_ids),
                "test_fraction": manifest.test_fraction,
                "cv_folds": manifest.cv_folds,
                "seed": manifest.random_seed,
                "split_fingerprint": manifest.split_fingerprint,
            },
            "limits": {
                "importance_features": 50,
                "importance_rows": 500,
                "importance_repeats": 5,
                "raw_training_data_included": False,
            },
        }

    def generate_html_report(self, experiment_id: str) -> Path:
        payload = self._report_payload(experiment_id)
        experiment = payload["experiment"]
        dataset = payload["dataset"]
        evaluation = payload["evaluation"]
        selected = payload["selected"]

        def escape(value: Any) -> str:
            return html.escape(str(value), quote=True)

        rows = []
        for trial in experiment.trials:
            score = "N/A" if trial.primary_cv_mean is None else f"{trial.primary_cv_mean:.6f}"
            rows.append(
                "<tr>"
                f"<td>{escape(trial.algorithm_id)}</td><td>{escape(trial.status)}</td>"
                f"<td>{score}</td><td>{trial.fit_duration_seconds:.3f}</td>"
                f"<td>{escape(trial.error or '')}</td></tr>"
            )
        importance_rows = "".join(
            "<tr>"
            f"<td>{escape(row['feature'])}</td><td>{row['mean_importance']:.6f}</td>"
            f"<td>{row['std_importance']:.6f}</td><td>{row['n_samples']}</td></tr>"
            for row in payload["importance"]
        )
        holdout = "Not finalized"
        exposure = "N/A"
        if evaluation:
            exposure = "Yes" if evaluation.holdout_previously_exposed else "No"
            holdout = escape(json.dumps([metric.model_dump(mode="json") for metric in evaluation.metrics]))
        content = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DataMind report — {escape(experiment.name)}</title>
<style>body{{font-family:Arial,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #bbb;padding:.45rem;text-align:left}}pre{{white-space:pre-wrap;background:#f4f4f4;padding:1rem}}.note{{background:#eef7ff;padding:1rem}}</style></head><body>
<h1>Experiment report: {escape(experiment.name)}</h1>
<p>Generated UTC: {escape(datetime.datetime.now(datetime.timezone.utc).isoformat())}</p>
<h2>Source and scope</h2><ul>
<li>Dataset: {escape(dataset.display_name)} ({escape(dataset.id)})</li><li>Raw SHA-256: {escape(dataset.raw_sha256)}</li>
<li>Task: {escape(experiment.task.value)}</li><li>Target: {escape(payload['target'])}</li>
<li>Development rows: {payload['split']['development_rows']}; holdout rows: {payload['split']['holdout_rows']}; CV folds: {payload['split']['cv_folds']}; seed: {payload['split']['seed']}</li>
<li>Selected model: {escape(selected.algorithm_id if selected else 'N/A')}</li><li>Holdout previously exposed: {exposure}</li></ul>
<h2>Actual resolved configuration</h2><pre>{escape(json.dumps(payload['config'], indent=2, sort_keys=True))}</pre>
<h2>Cleaning and limits</h2><pre>{escape(json.dumps({'cleaning_log': payload['config'].get('cleaning_log', []), 'parser': payload['parser'], 'limits': payload['limits']}, indent=2, sort_keys=True))}</pre>
<h2>Cross-validation trials and failures</h2><table><thead><tr><th>Algorithm</th><th>Status</th><th>Primary CV mean</th><th>Fit seconds</th><th>Failure</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Permutation importance — development-set diagnostic</h2><p class="note">Not independent evaluation and not causal evidence. Correlated features can obscure importance; negative values are legitimate. Seed 42, five repeats, at most 50 original features and 500 development rows.</p>
<table><thead><tr><th>Original feature</th><th>Mean change</th><th>Variation</th><th>Rows</th></tr></thead><tbody>{importance_rows}</tbody></table>
<h2>Holdout evaluation</h2><pre>{holdout}</pre>
<h2>Environment</h2><pre>{escape(json.dumps(payload['environment'], indent=2, sort_keys=True))}</pre>
<h2>Artifact hashes</h2><pre>{escape(json.dumps({'pipeline.joblib': compute_sha256_file(payload['model_path']), 'input_schema.json': compute_sha256_file(payload['schema_path'])}, indent=2))}</pre>
<p>Raw training data is excluded from exports by default.</p></body></html>"""
        path = get_settings().exports_dir / f"{experiment_id}_report.html"
        write_atomic_bytes(path, content.encode("utf-8"))
        return path

    def generate_markdown_report(self, experiment_id: str) -> Path:
        payload = self._report_payload(experiment_id)
        experiment = payload["experiment"]
        dataset = payload["dataset"]
        selected = payload["selected"]

        def safe(value: Any) -> str:
            return html.escape(str(value)).replace("|", "\\|").replace("\n", " ")

        lines = [
            f"# Experiment report: {safe(experiment.name)}",
            "",
            f"- Dataset: {safe(dataset.display_name)} (`{dataset.id}`)",
            f"- Raw SHA-256: `{dataset.raw_sha256}`",
            f"- Task: `{experiment.task.value}`",
            f"- Target: `{safe(payload['target'])}`",
            f"- Development rows: {payload['split']['development_rows']}",
            f"- Holdout rows: {payload['split']['holdout_rows']}",
            f"- CV folds: {payload['split']['cv_folds']}",
            f"- Selected model: `{safe(selected.algorithm_id if selected else 'N/A')}`",
            f"- Holdout previously exposed: {payload['evaluation'].holdout_previously_exposed if payload['evaluation'] else 'N/A'}",
            "",
            "## Actual resolved configuration",
            "```json",
            json.dumps(payload["config"], indent=2, sort_keys=True),
            "```",
            "",
            "## CV trials and failures",
            "| Algorithm | Status | Primary CV mean | Fit seconds | Failure |",
            "|---|---|---:|---:|---|",
        ]
        for trial in experiment.trials:
            score = "N/A" if trial.primary_cv_mean is None else f"{trial.primary_cv_mean:.6f}"
            lines.append(
                f"| {safe(trial.algorithm_id)} | {safe(trial.status)} | {score} | {trial.fit_duration_seconds:.3f} | {safe(trial.error or '')} |"
            )
        lines.extend(
            [
                "",
                "## Permutation importance — development-set diagnostic",
                "Not independent evaluation and **not causal evidence**. Correlated features can obscure importance; negative values are legitimate.",
                "",
                "| Original feature | Mean change | Variation | Rows |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in payload["importance"]:
            lines.append(
                f"| {safe(row['feature'])} | {row['mean_importance']:.6f} | {row['std_importance']:.6f} | {row['n_samples']} |"
            )
        lines.extend(
            [
                "",
                "## Holdout evaluation",
                "```json",
                json.dumps(
                    payload["evaluation"].model_dump(mode="json") if payload["evaluation"] else None,
                    indent=2,
                    sort_keys=True,
                ),
                "```",
                "",
                "## Environment",
                "```json",
                json.dumps(payload["environment"], indent=2, sort_keys=True),
                "```",
                "",
                "Raw training data is excluded from exports by default.",
            ]
        )
        path = get_settings().exports_dir / f"{experiment_id}_report.md"
        write_atomic_bytes(path, "\n".join(lines).encode("utf-8"))
        return path

    @staticmethod
    def _manifest(files: dict[str, tuple[bytes, str]], experiment_id: str) -> bytes:
        payload = {
            "experiment_id": experiment_id,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "raw_training_data_included": False,
            "files": {
                name: {
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "size_bytes": len(content),
                    "origin": origin,
                }
                for name, (content, origin) in files.items()
            },
        }
        return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")

    @staticmethod
    def _write_zip(path: Path, files: dict[str, tuple[bytes, str]], experiment_id: str) -> Path:
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            for name, (content, _origin) in files.items():
                bundle.writestr(name, content)
            bundle.writestr("manifest.json", ExportService._manifest(files, experiment_id))
        write_atomic_bytes(path, archive.getvalue())
        return path

    def create_model_zip(self, experiment_id: str) -> Path:
        evidence = self._collect(experiment_id)
        experiment = evidence["experiment"]
        metrics = self._metric_payload(experiment, evidence["evaluation"])
        readme = """# DataMind model export

This bundle excludes raw training data. `pipeline.joblib` contains a fitted scikit-learn pipeline.

Security: joblib/pickle deserialization can execute code. Load this file only when this trusted DataMind export has passed manifest checksum verification. Use a compatible Python and package environment from `environment.json`.
"""
        files = {
            "pipeline.joblib": (evidence["model_path"].read_bytes(), "saved champion artifact"),
            "input_schema.json": (evidence["schema_path"].read_bytes(), "saved fit-time schema"),
            "experiment_config.json": (
                json.dumps(evidence["config"], indent=2, sort_keys=True).encode(),
                "experiments.config_json",
            ),
            "metrics.json": (json.dumps(metrics, indent=2, sort_keys=True).encode(), "stored trials/evaluation"),
            "environment.json": (
                json.dumps(evidence["environment"], indent=2, sort_keys=True).encode(),
                "experiments.environment_json",
            ),
            "README.md": (readme.encode(), "generated safety and usage notes"),
        }
        path = get_settings().exports_dir / f"{experiment_id}_model.zip"
        return self._write_zip(path, files, experiment_id)

    def create_experiment_zip(self, experiment_id: str) -> Path:
        evidence = self._collect(experiment_id)
        html_path = self.generate_html_report(experiment_id)
        markdown_path = self.generate_markdown_report(experiment_id)
        metrics = self._metric_payload(evidence["experiment"], evidence["evaluation"])
        files = {
            "report.html": (html_path.read_bytes(), "generated from stored records"),
            "report.md": (markdown_path.read_bytes(), "generated from stored records"),
            "experiment_config.json": (
                json.dumps(evidence["config"], indent=2, sort_keys=True).encode(),
                "experiments.config_json",
            ),
            "metrics.json": (json.dumps(metrics, indent=2, sort_keys=True).encode(), "stored trials/evaluation"),
            "environment.json": (
                json.dumps(evidence["environment"], indent=2, sort_keys=True).encode(),
                "experiments.environment_json",
            ),
            "input_schema.json": (evidence["schema_path"].read_bytes(), "saved fit-time schema"),
        }
        path = get_settings().exports_dir / f"{experiment_id}_experiment.zip"
        return self._write_zip(path, files, experiment_id)
