"""Explore page: Modeling view confirmation, split generation, and development-only EDA."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from datamind.contracts import ColumnRole, ServiceError, TaskType
from datamind.services.datasets import DatasetService
from datamind.services.experiments import ExperimentService
from datamind.ui.components import (
    render_active_project_banner,
    render_header,
    render_service_error,
)
from datamind.ui.navigation import NavigationContext


def render_explore_page() -> None:
    """Render the Explore page."""
    render_header(
        title="Exploratory Data Analysis & Split Preparation",
        subtitle="Validate modeling roles, generate leakage-safe development/holdout splits, and explore development distributions",
    )
    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)

    if not active_project:
        return

    dataset_service = DatasetService()
    experiment_service = ExperimentService()

    datasets = dataset_service.list_datasets(active_project.id)
    if not datasets:
        st.info("No datasets available in this project. Please import or load a dataset on the Datasets page first.")
        return

    ds_options = {d.id: f"{d.display_name} ({d.row_count:,} rows, {d.column_count} cols)" for d in datasets}
    active_ds_id = st.session_state.get("active_dataset_id")
    selected_idx = 0
    if active_ds_id and active_ds_id in ds_options:
        selected_idx = list(ds_options.keys()).index(active_ds_id)

    selected_dataset_id = st.selectbox(
        "Select Dataset for Modeling & EDA",
        options=list(ds_options.keys()),
        index=selected_idx,
        format_func=lambda x: ds_options[x],
        key="explore_dataset_selector",
    )
    if NavigationContext.set_active_dataset(selected_dataset_id):
        st.rerun()

    dataset = dataset_service.get_dataset(selected_dataset_id)
    if not dataset:
        return

    schema = dataset.get_schema()
    col_names = schema.column_names

    st.markdown("### 1. Modeling Protocol Setup")
    st.caption("Confirm the prediction task, target variable, and feature roles before inspecting distributions.")

    col1, col2 = st.columns(2)
    with col1:
        task_choice = st.selectbox(
            "Target Task Type",
            options=[TaskType.CLASSIFICATION, TaskType.REGRESSION],
            format_func=lambda t: "Classification (Discrete classes)" if t == TaskType.CLASSIFICATION else "Regression (Continuous value)",
            key="explore_task_choice",
        )

    # Heuristic default target: last column or column suggested as target
    default_target_idx = len(col_names) - 1
    for i, col in enumerate(schema.columns):
        if col.name.lower() in ("target", "label", "class", "species"):
            default_target_idx = i
            break

    with col2:
        target_choice = st.selectbox(
            "Target Column",
            options=col_names,
            index=default_target_idx,
            key="explore_target_choice",
        )

    # Feature selection
    feature_candidates = [c for c in col_names if c != target_choice]
    numeric_candidates = [
        c.name for c in schema.columns
        if c.name in feature_candidates and c.suggested_role == ColumnRole.NUMERIC
    ]
    categorical_candidates = [
        c.name for c in schema.columns
        if c.name in feature_candidates and c.suggested_role != ColumnRole.NUMERIC
    ]

    f_col1, f_col2 = st.columns(2)
    with f_col1:
        selected_numeric = st.multiselect(
            "Numeric Features",
            options=feature_candidates,
            default=numeric_candidates,
            key="explore_numeric_features",
        )
    with f_col2:
        selected_categorical = st.multiselect(
            "Categorical Features",
            options=[c for c in feature_candidates if c not in selected_numeric],
            default=[c for c in categorical_candidates if c not in selected_numeric],
            key="explore_categorical_features",
        )

    # Split parameters
    st.markdown("### 2. Leakage-Guarded Split Configuration")
    st.caption("Holdout rows are completely sequestered. Cross-validation folds are created deterministically.")

    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        test_frac = st.selectbox(
            "Holdout Fraction",
            options=[0.20, 0.25],
            format_func=lambda f: f"{int(f * 100)}% Holdout (Sequestered)",
            index=0,
            key="explore_test_frac",
        )
    with s_col2:
        cv_folds = st.selectbox(
            "Cross-Validation Folds",
            options=[5, 3],
            format_func=lambda k: f"{k} Folds",
            index=0,
            key="explore_cv_folds",
        )
    with s_col3:
        random_seed = st.number_input(
            "Random Split Seed",
            min_value=0,
            max_value=999999,
            value=42,
            step=1,
            key="explore_random_seed",
        )

    # Build view and split keys from the complete current draft configuration.
    draft_signature = hash(
        (
            dataset.id,
            target_choice,
            task_choice.value,
            tuple(selected_numeric),
            tuple(selected_categorical),
            test_frac,
            cv_folds,
            int(random_seed),
        )
    )
    view_key = f"view_{draft_signature}"
    split_key = f"split_{draft_signature}"

    if st.button("Prepare Verified Split & Generate Development EDA", type="primary"):
        try:
            with st.spinner("Validating modeling view and computing split manifest..."):
                view = experiment_service.prepare_modeling_view(
                    dataset_id=dataset.id,
                    task=task_choice,
                    target=target_choice,
                    numeric_features=selected_numeric,
                    categorical_features=selected_categorical,
                )
                manifest = experiment_service.prepare_split(
                    dataset_id=dataset.id,
                    view=view,
                    test_fraction=test_frac,
                    cv_folds=cv_folds,
                    random_seed=int(random_seed),
                )
            st.session_state[view_key] = view
            st.session_state[split_key] = manifest
            st.success(f"Split verified! Development set: **{len(manifest.train_row_ids):,} rows**, Holdout set: **{len(manifest.test_row_ids):,} rows** (Strictly Disjoint)")
        except ServiceError as err:
            render_service_error(err)
        except Exception as exc:
            st.error(f"Failed to prepare split: {exc}")

    # Render EDA if split exists in session state
    if split_key in st.session_state and view_key in st.session_state:
        view = st.session_state[view_key]
        manifest = st.session_state[split_key]

        st.divider()
        st.subheader("📈 Development Data Exploratory Analysis")
        st.warning(
            "🔒 **Strict Leakage Prevention Guarantee**: All metrics, histograms, and correlations shown below "
            f"are computed **strictly on the {len(manifest.train_row_ids)} development rows**. "
            f"The {len(manifest.test_row_ids)} holdout rows are sequestered and completely hidden from this view."
        )

        df = dataset_service.load_dataframe(dataset.id)
        dev_df = df.loc[manifest.train_row_ids]

        # Target distribution
        st.markdown(f"#### Target Distribution: `{view.target}` (Development Set)")
        if view.task == TaskType.CLASSIFICATION:
            class_counts = dev_df[view.target].value_counts().reset_index()
            class_counts.columns = [view.target, "Count"]
            fig_target = px.bar(
                class_counts,
                x=view.target,
                y="Count",
                title=f"Class Frequencies on Development Rows (N={len(dev_df)})",
                color=view.target,
            )
            st.plotly_chart(fig_target, use_container_width=True)
        else:
            fig_target = px.histogram(
                dev_df,
                x=view.target,
                nbins=30,
                title=f"Continuous Target Histogram on Development Rows (N={len(dev_df)})",
                marginal="box",
            )
            st.plotly_chart(fig_target, use_container_width=True)

        # Feature distributions
        if view.numeric_features:
            st.markdown("#### Numeric Feature Distributions (Development Set)")
            chosen_feat = st.selectbox(
                "Select numeric feature to inspect",
                options=view.numeric_features,
                key="eda_feat_select",
            )
            if view.task == TaskType.CLASSIFICATION:
                fig_feat = px.histogram(
                    dev_df,
                    x=chosen_feat,
                    color=view.target,
                    barmode="overlay",
                    nbins=25,
                    title=f"Distribution of '{chosen_feat}' by '{view.target}' (Development Rows)",
                )
            else:
                fig_feat = px.scatter(
                    dev_df,
                    x=chosen_feat,
                    y=view.target,
                    title=f"Scatter: '{chosen_feat}' vs '{view.target}' (Development Rows)",
                    trendline="ols",
                )
            st.plotly_chart(fig_feat, use_container_width=True)

            # Correlation Heatmap
            if len(view.numeric_features) >= 2:
                st.markdown("#### Numeric Features Correlation Heatmap (Development Set)")
                st.caption("Pearson correlation coefficients computed strictly on development rows. Correlation indicates association, not causation.")
                corr_cols = view.numeric_features.copy()
                if view.task == TaskType.REGRESSION and view.target not in corr_cols:
                    corr_cols.append(view.target)
                corr_matrix = dev_df[corr_cols].corr()
                fig_corr = px.imshow(
                    corr_matrix,
                    text_auto=".2f",
                    aspect="auto",
                    color_continuous_scale="RdBu_r",
                    zmin=-1.0,
                    zmax=1.0,
                    title="Correlation Matrix (Development Rows Only)",
                )
                st.plotly_chart(fig_corr, use_container_width=True)

        st.info("Split manifest and modeling view are ready! Proceed to the **Experiment** page to train models.")
