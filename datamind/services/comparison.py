"""Comparison service: verifies compatibility and compiles multi-experiment leaderboards."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from datamind.contracts import (
    ComparisonResult,
    ErrorCode,
    ExperimentSummary,
    ServiceError,
)
from datamind.services.experiments import ExperimentService


class ComparisonService:
    """Service to validate experiment compatibility and generate consistent comparative leaderboards."""

    def __init__(self, experiment_service: Optional[ExperimentService] = None):
        self.experiment_service = experiment_service or ExperimentService()

    def compare(self, experiment_ids: List[str]) -> ComparisonResult:
        """
        Compare two or more completed experiments.

        Enforces strict comparability:
        - Must share identical task, target, split fingerprint, and primary metric.
        - If any field mismatches, raises ServiceError(INCOMPATIBLE_COMPARISON).
        """
        if not experiment_ids or len(experiment_ids) < 2:
            raise ServiceError(
                ErrorCode.INCOMPATIBLE_COMPARISON,
                "At least two experiments are required for comparison.",
            )

        experiments: List[ExperimentSummary] = []
        for eid in experiment_ids:
            exp = self.experiment_service.get_experiment(eid)
            if exp is None:
                raise ServiceError(
                    ErrorCode.INVALID_MODEL_CONFIG,
                    f"Experiment '{eid}' not found.",
                )
            if exp.task.value == "clustering":
                raise ServiceError(
                    ErrorCode.INCOMPATIBLE_COMPARISON,
                    "Clustering experiments are exploratory and are not ranked in the supervised comparison leaderboard.",
                )
            if exp.status != "completed":
                raise ServiceError(
                    ErrorCode.INCOMPATIBLE_COMPARISON,
                    f"Experiment '{eid}' is in state '{exp.status}'. Only completed experiments can be compared.",
                )
            experiments.append(exp)

        # Baseline reference is the first experiment
        base = experiments[0]
        mismatches: List[str] = []

        for other in experiments[1:]:
            if other.task != base.task:
                mismatches.append(f"Task mismatch ({base.name}: {base.task.value} vs {other.name}: {other.task.value})")
            if other.primary_metric != base.primary_metric:
                mismatches.append(f"Primary metric mismatch ({base.primary_metric} vs {other.primary_metric})")
            if other.dataset_id != base.dataset_id:
                mismatches.append(f"Dataset mismatch ({base.dataset_id} vs {other.dataset_id})")

            # Check split / comparison_key compatibility
            if other.comparison_key != base.comparison_key:
                mismatches.append(f"Split/Cohort fingerprint mismatch between '{base.name}' and '{other.name}'")

        if mismatches:
            raise ServiceError(
                ErrorCode.INCOMPATIBLE_COMPARISON,
                f"Cannot compare incompatible experiments: {'; '.join(mismatches)}",
                details={"mismatches": mismatches},
            )

        # Compile leaderboard table rows
        table_rows: List[Dict[str, Any]] = []
        config_diffs: List[Dict[str, Any]] = []

        for exp in experiments:
            champ_trial = None
            if exp.selected_trial_id:
                for t in exp.trials:
                    if t.trial_id == exp.selected_trial_id:
                        champ_trial = t
                        break

            cv_mean = champ_trial.primary_cv_mean if champ_trial else None
            cv_std = champ_trial.primary_cv_std if champ_trial else None
            champ_algo = champ_trial.algorithm_id if champ_trial else "None"
            dur = sum(t.fit_duration_seconds for t in exp.trials)

            table_rows.append({
                "experiment_id": exp.id,
                "experiment_name": exp.name,
                "champion_algorithm": champ_algo,
                "primary_metric": exp.primary_metric,
                "cv_mean": cv_mean,
                "cv_std": cv_std,
                "total_fit_duration": dur,
                "trials_count": len(exp.trials),
                "started_at": exp.started_at,
            })

            try:
                cfg = json.loads(exp.config_json)
            except Exception:
                cfg = {}

            config_diffs.append({
                "experiment_id": exp.id,
                "experiment_name": exp.name,
                "prep_config": cfg.get("prep_config", {}),
                "seed": exp.random_seed,
                "algorithms": [a.get("algorithm_id") for a in cfg.get("algorithm_configs", [])],
            })

        # Sort table_rows by cv_mean (higher is better for classification, lower for regression)
        reverse_sort = (base.task.value == "classification")
        table_rows.sort(
            key=lambda r: (r["cv_mean"] is not None, r["cv_mean"] if r["cv_mean"] is not None else 0.0),
            reverse=reverse_sort,
        )

        return ComparisonResult(
            is_compatible=True,
            primary_metric=base.primary_metric,
            candidate_experiment_ids=experiment_ids,
            table_rows=table_rows,
            mismatch_reasons=[],
            config_differences=config_diffs,
        )
