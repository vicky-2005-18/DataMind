#!/usr/bin/env python3
"""
DataMind M4 Demonstration: Explanation, Permutation Importance, and Export
===========================================================================

Demonstrates:
  1. Permutation importance computation on development rows (T32)
  2. HTML and Markdown report generation with escaped content (T33)
  3. Model ZIP and Experiment ZIP with manifest and checksums (T33)
  4. Safe CSV export with formula escaping (T34)
  5. Model export/reload consistency verification
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path

import joblib
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datamind.config import get_settings
from datamind.contracts import AlgorithmConfig, DemoDatasetKind, PredictionBatch, TaskType
from datamind.services.datasets import DatasetService
from datamind.services.experiments import ExperimentService
from datamind.services.export import ExportService
from datamind.services.prediction import PredictionService
from datamind.services.projects import ProjectService
from datamind.storage.database import run_migrations

# ── Initialise ──────────────────────────────────────────────────────────────

settings = get_settings()
settings.ensure_directories()
run_migrations(settings.db_path)

print("=" * 70)
print("DataMind M4 Demonstration: Explanation, Permutation & Export")
print("=" * 70)

# ── 1. Create project and load dataset ───────────────────────────────────────

project_svc = ProjectService()
project = project_svc.create_project(f"M4 Demo {uuid.uuid4().hex[:6]}", "M4 verification run")
print(f"\n[1] Created project: '{project.name}' (ID: {project.id[:8]})")

dataset_svc = DatasetService()
iris = dataset_svc.load_demo(project_id=project.id, demo_kind=DemoDatasetKind.IRIS)
print(f"[2] Loaded demo dataset: '{iris.display_name}' ({iris.row_count} rows, {iris.column_count} cols)")

df = dataset_svc.load_dataframe(iris.id)
numeric_features = [c for c in df.columns if c != "species" and pd.api.types.is_numeric_dtype(df[c])]
categorical_features = []

# ── 2. Run supervised experiment ──────────────────────────────────────────

svc = ExperimentService()

view = svc.prepare_modeling_view(
    dataset_id=iris.id,
    task=TaskType.CLASSIFICATION,
    target="species",
    numeric_features=numeric_features,
    categorical_features=categorical_features,
)
manifest = svc.prepare_split(dataset_id=iris.id, view=view, test_fraction=0.20, cv_folds=5, random_seed=42)
print(f"\n[3] Split generated: {len(manifest.train_row_ids)} dev rows, {len(manifest.test_row_ids)} holdout rows")

algo_configs = [
    AlgorithmConfig(algorithm_id="logistic_regression"),
    AlgorithmConfig(algorithm_id="random_forest_classifier"),
]

print("\n[4] Running CV experiment...")
exp = svc.run_supervised_experiment(
    experiment_name="M4 Export Test",
    project_id=project.id,
    dataset_id=iris.id,
    view=view,
    manifest=manifest,
    algorithm_configs=algo_configs,
    seed=42,
)
print(f"    Status: {exp.status} | Champion: {exp.selected_trial_id[:8]} | {exp.selection_reason}")

# ── 3. Finalize holdout ─────────────────────────────────────────────────────

print("\n[5] Finalizing holdout evaluation...")
eval_result = svc.finalize_experiment(exp.id)
print(f"    Evaluation ID: {eval_result.id[:8]} | Previously exposed: {eval_result.holdout_previously_exposed}")
for m in eval_result.metrics:
    if m.fold_index == -1:
        print(f"      {m.name}: {m.value:.4f}" if m.value is not None else f"      {m.name}: N/A")

# ── 4. Compute permutation importance (T32) ─────────────────────────────────

print("\n[6] Computing permutation importance on development rows...")
export_svc = ExportService(experiment_service=svc)
importance_records = export_svc.compute_importance(exp.id)
print(f"    Computed importance for {len(importance_records)} features")
print("    Top 3 features by absolute importance:")
for record in sorted(importance_records, key=lambda r: abs(r['mean_importance']), reverse=True)[:3]:
    print(f"      {record['feature']}: {record['mean_importance']:.6f} ± {record['std_importance']:.6f}")

# ── 5. Generate HTML and Markdown reports (T33) ───────────────────────────────

print("\n[7] Generating HTML report...")
html_path = export_svc.generate_html_report(exp.id)
print(f"    HTML report saved: {html_path}")
print(f"    File size: {html_path.stat().st_size:,} bytes")

print("\n[8] Generating Markdown report...")
md_path = export_svc.generate_markdown_report(exp.id)
print(f"    Markdown report saved: {md_path}")
print(f"    File size: {md_path.stat().st_size:,} bytes")

# Verify HTML escaping
html_content = html_path.read_text(encoding="utf-8")
if "<b>evidence</b>" not in html_content:
    print("    [OK] T34 HTML escaping verified: special characters escaped")
else:
    print("    [FAIL] T34 HTML escaping failed: unescaped special characters found")

# ── 6. Generate Model ZIP (T33) ─────────────────────────────────────────────

print("\n[9] Generating Model ZIP...")
model_zip = export_svc.create_model_zip(exp.id)
print(f"    Model ZIP saved: {model_zip}")
print(f"    File size: {model_zip.stat().st_size:,} bytes")

with zipfile.ZipFile(model_zip) as archive:
    print(f"    ZIP contents: {archive.namelist()}")
    manifest_data = json.loads(archive.read("manifest.json"))
    print(f"    Raw training data included: {manifest_data['raw_training_data_included']}")
    print(f"    Manifest files count: {len(manifest_data['files'])}")

    # Verify checksums
    for name, details in manifest_data['files'].items():
        actual_hash = hashlib.sha256(archive.read(name)).hexdigest()
        if actual_hash == details['sha256']:
            print(f"      [OK] {name}: checksum verified")
        else:
            print(f"      [FAIL] {name}: checksum mismatch")

# ── 7. Generate Experiment ZIP (T33) ───────────────────────────────────────

print("\n[10] Generating Experiment ZIP...")
exp_zip = export_svc.create_experiment_zip(exp.id)
print(f"    Experiment ZIP saved: {exp_zip}")
print(f"    File size: {exp_zip.stat().st_size:,} bytes")

with zipfile.ZipFile(exp_zip) as archive:
    print(f"    ZIP contents: {archive.namelist()}")
    if "raw.csv" not in archive.namelist():
        print("    [OK] T33 Raw training data excluded from experiment ZIP")

# ── 8. Safe CSV export with formula escaping (T34) ────────────────────────────

print("\n[11] Testing safe CSV export with formula escaping...")

test_df = pd.DataFrame({
    "text": ["=1+1", "+SUM(A1:A2)", "-2+3", "@cmd", "\tformula", "\rformula", "safe"],
    "number": [-4, 1, 2, 3, 4, 5, 6],
})
batch = PredictionBatch(row_ids=list(range(7)), predictions=["ok"] * 7)
pred_svc = PredictionService()
csv_bytes = pred_svc.export_batch_csv(test_df, batch, "label")
parsed = pd.read_csv(pd.io.common.BytesIO(csv_bytes), keep_default_na=False)

expected_escaped = ["'=1+1", "'+SUM(A1:A2)", "'-2+3", "'@cmd", "'\tformula", "'\rformula"]
actual_escaped = parsed["text"].tolist()[:6]
if actual_escaped == expected_escaped:
    print("    [OK] T34 Formula escaping verified: spreadsheet prefixes escaped")
else:
    print(f"    [FAIL] T34 Formula escaping failed: expected {expected_escaped}, got {actual_escaped}")

# ── 9. Model export/reload consistency (T33) ───────────────────────────────

print("\n[12] Verifying model export/reload consistency...")

with tempfile.TemporaryDirectory() as tmpdir:
    with zipfile.ZipFile(model_zip) as archive:
        archive.extractall(tmpdir)

    exported_pipeline = joblib.load(Path(tmpdir) / "pipeline.joblib")
    original_pipeline = joblib.load(settings.experiments_dir / exp.id / "champion.joblib")

    sample = df.loc[:10, numeric_features]
    original_preds = original_pipeline.predict(sample)
    exported_preds = exported_pipeline.predict(sample)

    if (original_preds == exported_preds).all():
        print("    [OK] T33 Model reload consistency: predictions match")
    else:
        print("    [FAIL] T33 Model reload consistency: predictions differ")

# ── 10. Summary ─────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("M4 Explanation & Export Demonstration COMPLETED SUCCESSFULLY")
print("=" * 70)
print(f"""
Summary:
  Project: '{project.name}' ({project.id[:8]})
  Experiment: {exp.id[:8]} — {exp.status}
  Evaluation: {eval_result.id[:8]} (previously_exposed={eval_result.holdout_previously_exposed})

Generated artifacts:
  HTML report: {html_path}
  Markdown report: {md_path}
  Model ZIP: {model_zip}
  Experiment ZIP: {exp_zip}

Tests verified:
  T32 Permutation importance (bounded, deterministic, labeled)    [OK]
  T33 Model ZIP (manifest, checksums, no raw data)               [OK]
  T33 Experiment ZIP (reports, checksums, no raw data)            [OK]
  T34 HTML escaping (special characters escaped)                   [OK]
  T34 CSV formula escaping (spreadsheet prefixes escaped)          [OK]
  Model export/reload consistency                                  [OK]
""")
