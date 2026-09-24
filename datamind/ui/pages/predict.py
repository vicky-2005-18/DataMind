"""Predict page: single-row manual input and bounded CSV batch inference (M3)."""

from __future__ import annotations

import io
import json
from typing import Optional

import pandas as pd
import streamlit as st

from datamind.config import get_settings
from datamind.contracts import ServiceError
from datamind.services.experiments import ExperimentService
from datamind.services.prediction import MAX_PREDICTION_ROWS, PredictionService
from datamind.ui.components import (
    render_active_project_banner,
    render_header,
    render_service_error,
)
from datamind.ui.navigation import NavigationContext


def _load_input_schema(experiment_id: str) -> Optional[dict]:
    """Load the input_schema.json saved during champion refit."""
    settings = get_settings()
    schema_file = settings.experiments_dir / experiment_id / "input_schema.json"
    if schema_file.exists():
        with open(schema_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def render_predict_page() -> None:
    """Render the Predict page."""
    render_header(
        title="Model Prediction",
        subtitle="Generate single-row or CSV batch predictions using fitted, validated champion pipelines",
    )
    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)

    if not active_project:
        return

    experiment_service = ExperimentService()
    prediction_service = PredictionService()

    all_experiments = experiment_service.list_experiments(active_project.id)
    # Only experiments with a persisted champion artifact are usable for prediction
    settings = get_settings()
    usable_exps = [
        e for e in all_experiments
        if e.status == "completed"
        and e.selected_trial_id
        and (settings.experiments_dir / e.id / "champion.joblib").exists()
        and (settings.experiments_dir / e.id / "input_schema.json").exists()
    ]

    if not usable_exps:
        st.info(
            "No finalized champion models available. "
            "Run an experiment on the **Supervised Experiments** page to create one."
        )
        return

    exp_options = {
        e.id: f"{e.name} [{e.id[:8]}] — Task: {e.task.value} — Metric: {e.primary_metric}"
        for e in usable_exps
    }

    selected_exp_id = st.selectbox(
        "Select Champion Model",
        options=list(exp_options.keys()),
        format_func=lambda eid: exp_options[eid],
        key="predict_exp_selector",
    )

    schema = _load_input_schema(selected_exp_id)
    if schema is None:
        st.error("Input schema for this model is missing. Please retrain the experiment.")
        return

    feature_names: list = schema["feature_names"]
    numeric_features: list = schema["numeric_features"]
    categorical_features: list = schema.get("categorical_features", [])
    target_name: str = schema.get("target", "prediction")
    task: str = schema.get("task", "classification")

    st.success(
        f"✅ **Model loaded** — {len(feature_names)} input features: "
        f"{len(numeric_features)} numeric, {len(categorical_features)} categorical. "
        f"Target: `{target_name}` | Task: `{task}`"
    )

    # ── Prediction Mode ───────────────────────────────────────────────
    predict_mode = st.radio(
        "Prediction Mode",
        options=["Single Row (manual input)", "Batch CSV Upload"],
        horizontal=True,
        key="predict_mode_radio",
    )

    input_df: Optional[pd.DataFrame] = None
    should_predict = False

    if predict_mode == "Single Row (manual input)":
        st.markdown("#### Enter Feature Values")
        st.caption("Fill in each feature value. Leave blank to treat as missing; the saved pipeline will impute it.")
        row_values = {}
        with st.form("predict_single_form"):
            for feat in feature_names:
                field_type = "numeric" if feat in numeric_features else "text"
                row_values[feat] = st.text_input(
                    f"{feat} ({field_type})",
                    key=f"pred_feat_{feat}",
                )
            should_predict = st.form_submit_button("Predict Single Row", type="primary")

        if should_predict:
            parsed_values = {}
            invalid_fields = []
            for feat, value in row_values.items():
                if not value.strip():
                    parsed_values[feat] = None
                elif feat in numeric_features:
                    try:
                        parsed_values[feat] = float(value)
                    except ValueError:
                        invalid_fields.append(feat)
                else:
                    parsed_values[feat] = value
            if invalid_fields:
                st.error(f"Enter valid numbers for: {', '.join(invalid_fields)}.")
                should_predict = False
            else:
                input_df = pd.DataFrame([parsed_values])

    else:
        st.markdown(f"#### Upload CSV (max {MAX_PREDICTION_ROWS:,} rows)")
        st.caption(
            f"Upload a CSV with the same columns as the training features. "
            f"Expected columns: `{', '.join(feature_names[:5])}{'...' if len(feature_names) > 5 else ''}`"
        )
        uploaded_file = st.file_uploader(
            "Choose a CSV file for batch prediction",
            type=["csv"],
            key="predict_batch_uploader",
        )
        if uploaded_file is not None:
            try:
                raw_bytes = uploaded_file.read()
                # Strip BOM if present
                if raw_bytes.startswith(b"\xef\xbb\xbf"):
                    raw_bytes = raw_bytes[3:]
                input_df = pd.read_csv(io.BytesIO(raw_bytes))
                st.success(f"Loaded {len(input_df):,} rows × {len(input_df.columns)} columns.")
                st.dataframe(input_df.head(5), use_container_width=True, hide_index=True)
            except Exception as exc:
                st.error(f"Failed to read CSV: {exc}")
                input_df = None

        if input_df is not None:
            should_predict = st.button(
                "Run Batch Prediction",
                type="primary",
                key="predict_batch_btn",
            )

    if input_df is not None and should_predict:
        try:
            with st.spinner("Running inference with saved champion pipeline..."):
                batch = prediction_service.predict(
                    experiment_id=selected_exp_id,
                    input_df=input_df,
                    exclude_extra_columns=True,
                )

            st.divider()
            st.subheader("🎯 Prediction Results")

            # Build results table
            result_df = input_df.copy()
            result_df[f"predicted_{target_name}"] = batch.predictions

            if batch.probabilities and batch.classes:
                for i, cls_name in enumerate(batch.classes):
                    result_df[f"prob_{cls_name}"] = [row[i] for row in batch.probabilities]

            st.dataframe(result_df, use_container_width=True, hide_index=True)

            # Warnings
            if batch.warnings:
                for w in batch.warnings:
                    st.warning(f"⚠️ {w}")

            # CSV download
            csv_bytes = prediction_service.export_batch_csv(input_df, batch, target_name)
            st.download_button(
                label="⬇️ Download Predictions as CSV",
                data=csv_bytes,
                file_name=f"predictions_{selected_exp_id[:8]}_{target_name}.csv",
                mime="text/csv",
                key="predict_download_btn",
            )

        except ServiceError as err:
            render_service_error(err)
        except Exception as exc:
            st.error(f"Prediction failed: {exc}")
