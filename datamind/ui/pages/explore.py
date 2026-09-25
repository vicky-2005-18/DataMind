"""Explore page: Modeling view confirmation, split generation, and development-only EDA."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from datamind.contracts import ColumnRole, ServiceError, TaskType
from datamind.services.datasets import DatasetService
from datamind.services.experiments import ExperimentService
from datamind.ui.components import (
    pill_html,
    render_active_project_banner,
    render_header,
    render_service_error,
    render_split_bar,
    render_workflow_stepper,
    style_plotly_figure,
)
from datamind.ui.navigation import NavigationContext


def render_explore_page() -> None:
    """Render the Explore page."""
    render_header(
        title="Exploratory Data Analysis & Split Preparation",
        subtitle="Validate modeling roles, generate leakage-safe development/holdout splits, and explore development distributions",
    )
    render_workflow_stepper("Prepare")
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
            help="Percentage of rows withheld as final test set. Example: 20% = 150 rows withheld from 750 total.",
        )
    with s_col2:
        cv_folds = st.selectbox(
            "Cross-Validation Folds",
            options=[5, 3],
            format_func=lambda k: f"{k} Folds",
            index=0,
            key="explore_cv_folds",
            help="Number of folds for cross-validation. 5 folds: each fold is 20% of development set.",
        )
    with s_col3:
        random_seed = st.number_input(
            "Random Split Seed",
            min_value=0,
            max_value=999999,
            value=42,
            step=1,
            key="explore_random_seed",
            help="Seed for reproducible split generation. Same seed always produces the same split.",
        )

    # Planned partition preview from the real row count and chosen holdout fraction
    planned_holdout = int(round(dataset.row_count * test_frac))
    planned_dev = dataset.row_count - planned_holdout
    st.markdown("#### Planned Partition")
    render_split_bar(planned_dev, planned_holdout)

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

        # Scope header
        st.markdown(
            f"**Dataset:** {dataset.display_name} | **Task:** {view.task.value.title()} | "
            f"**Target:** `{view.target}` | **Development rows:** {len(manifest.train_row_ids):,}"
        )
        st.markdown("#### Verified Partition")
        render_split_bar(len(manifest.train_row_ids), len(manifest.test_row_ids))
        st.markdown("### Development Data Exploratory Analysis")
        st.warning(
            "**Strict Leakage Prevention**: All analysis below uses only the development set. "
            f"The {len(manifest.test_row_ids):,} holdout rows are sequestered."
        )

        df = dataset_service.load_dataframe(dataset.id)
        dev_df = df.loc[manifest.train_row_ids]

        # Development diagnostics: class balance or target skew
        if view.task == TaskType.CLASSIFICATION:
            class_share = dev_df[view.target].value_counts(normalize=True)
            majority_share = float(class_share.iloc[0])
            majority_class = class_share.index[0]
            if majority_share > 0.70:
                st.markdown(
                    pill_html(
                        f"Imbalance risk: majority class '{majority_class}' holds {majority_share:.1%} of dev rows",
                        "amber",
                    ),
                    unsafe_allow_html=True,
                )
                st.caption(
                    "Severe imbalance can inflate raw accuracy. Consider balanced accuracy or F1 as the primary metric."
                )
            else:
                st.markdown(
                    pill_html(
                        f"Class balance acceptable: largest class holds {majority_share:.1%} of dev rows",
                        "success",
                    ),
                    unsafe_allow_html=True,
                )
        else:
            target_skew = float(dev_df[view.target].skew())
            if abs(target_skew) > 1.0:
                direction = "Right-skewed" if target_skew > 0 else "Left-skewed"
                skew_pill = pill_html(f"Target skew: {target_skew:.2f} — {direction}", "amber")
                skew_note = (
                    "Strongly skewed targets can degrade RMSE/MAE ranking stability. "
                    "Review the histogram below before training."
                )
            else:
                skew_pill = pill_html(f"Target skew: {target_skew:.2f} — approximately symmetric", "success")
                skew_note = "Skewness within ±1.0 usually needs no target transformation."
            st.markdown(skew_pill, unsafe_allow_html=True)
            st.caption(f"{skew_note} Computed on development rows only.")

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
                color_discrete_sequence=["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#f43f5e"],
            )
            # Let Plotly use its default hover template for categorical data
            # This ensures proper legend grouping and tooltip display
            fig_target = style_plotly_figure(fig_target)
            st.plotly_chart(fig_target, width='stretch')
        else:
            fig_target = px.histogram(
                dev_df,
                x=view.target,
                nbins=30,
                title=f"Continuous Target Histogram on Development Rows (N={len(dev_df)})",
                marginal="box",
                color_discrete_sequence=["#6366f1"],
            )
            fig_target.update_traces(
                hovertemplate="%{x} — Count: %{y}<extra></extra>",
                selector=dict(type="histogram"),
            )
            fig_target = style_plotly_figure(fig_target)
            st.plotly_chart(fig_target, width='stretch')

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
                    color_discrete_sequence=["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#f43f5e"],
                )
                fig_feat.update_traces(
                    hovertemplate="%{x} — %{y}<extra></extra>",
                    selector=dict(type="histogram"),
                )
            else:
                fig_feat = px.scatter(
                    dev_df,
                    x=chosen_feat,
                    y=view.target,
                    title=f"Scatter: '{chosen_feat}' vs '{view.target}' (Development Rows)",
                    trendline="ols",
                    color_discrete_sequence=["#6366f1"],
                )
                fig_feat.update_traces(
                    hovertemplate=f"%{{x}} — {view.target}: %{{y}}<extra></extra>",
                    selector=dict(type="scatter"),
                )
            fig_feat = style_plotly_figure(fig_feat)
            st.plotly_chart(fig_feat, width='stretch')

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
                fig_corr = style_plotly_figure(fig_corr)
                st.plotly_chart(fig_corr, width='stretch')

                # Collinearity auto-flagging from the same development-only matrix
                collinear_pairs = []
                for i in range(len(corr_cols)):
                    for j in range(i + 1, len(corr_cols)):
                        value = corr_matrix.iloc[i, j]
                        if pd.notna(value) and abs(value) > 0.9:
                            collinear_pairs.append((corr_cols[i], corr_cols[j], float(value)))
                if collinear_pairs:
                    with st.expander(
                        f"Highly collinear feature pairs (|r| > 0.9) — {len(collinear_pairs)}",
                        expanded=True,
                    ):
                        for feat_a, feat_b, value in collinear_pairs:
                            st.markdown(
                                pill_html(f"{feat_a} ↔ {feat_b}: r = {value:.3f}", "amber"),
                                unsafe_allow_html=True,
                            )
                        st.caption(
                            "Near-duplicate features can split permutation importance and destabilize "
                            "linear coefficients. Dropping one of each pair is usually safe for tree models."
                        )
                else:
                    st.markdown(
                        pill_html("No feature pairs exceed |r| > 0.9 on development rows", "success"),
                        unsafe_allow_html=True,
                    )

        st.info("Split manifest and modeling view are ready! Proceed to the **Experiment** page to train models.")
