"""Numeric K-Means clustering lab with persisted diagnostics."""

from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from datamind.services.clustering import ClusteringService
from datamind.services.datasets import DatasetService
from datamind.ui.components import render_active_project_banner, render_header, render_service_error
from datamind.ui.navigation import NavigationContext


def render_clustering_page() -> None:
    """Render the persisted numeric K-Means workflow."""
    render_header(
        title="Unsupervised Clustering Lab",
        subtitle="Fit K-Means in standardized feature space and inspect bounded exploratory diagnostics",
    )
    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)
    if not active_project:
        return

    dataset_service = DatasetService()
    clustering_service = ClusteringService(dataset_service=dataset_service)
    datasets = dataset_service.list_datasets(active_project.id)
    if not datasets:
        st.info("Load a dataset before running the clustering lab.")
        return

    dataset_options = {dataset.id: dataset.display_name for dataset in datasets}
    dataset_id = st.selectbox(
        "Dataset",
        options=list(dataset_options),
        format_func=lambda value: dataset_options[value],
    )
    frame = dataset_service.load_dataframe(dataset_id)
    numeric_columns = frame.select_dtypes(include="number").columns.tolist()
    if len(numeric_columns) < 2:
        st.error("This dataset does not contain at least two numeric columns.")
        return

    with st.form("clustering_form"):
        experiment_name = st.text_input("Experiment name", value="K-Means exploration")
        features = st.multiselect(
            "Numeric features",
            options=numeric_columns,
            default=numeric_columns[: min(3, len(numeric_columns))],
        )
        k = st.slider("Number of clusters (k)", min_value=2, max_value=10, value=3)
        seed = st.number_input("Random seed", min_value=0, max_value=2_147_483_647, value=42)
        submitted = st.form_submit_button("Run K-Means", type="primary")

    if submitted:
        try:
            result = clustering_service.run_experiment(
                project_id=active_project.id,
                dataset_id=dataset_id,
                experiment_name=experiment_name,
                feature_names=features,
                k=k,
                seed=int(seed),
            )
            st.session_state["clustering_result_id"] = result.experiment.id
        except Exception as exc:
            render_service_error(exc)

    result_id = st.session_state.get("clustering_result_id")
    if not result_id:
        st.info("Run K-Means explicitly to generate real fitted outputs. No target or accuracy metric is used.")
        return

    try:
        result = clustering_service.load_result(result_id)
    except Exception as exc:
        render_service_error(exc)
        return
    if result.experiment.dataset_id != dataset_id:
        st.info("The selected dataset changed. Run K-Means again for this dataset.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Inertia", f"{result.inertia:.3f}")
    col2.metric("Silhouette", f"{result.silhouette:.3f}" if result.silhouette is not None else "N/A")
    col3.metric("Rows clustered", f"{sum(result.cluster_sizes.values()):,}")
    st.caption(
        "Silhouette is computed in the median-imputed, standardized modeling feature space. "
        f"The seeded sample contains {result.silhouette_sample_size:,} rows."
    )
    if result.silhouette_reason:
        st.info(result.silhouette_reason)
    for warning in result.warnings:
        st.warning(warning)

    sizes = pd.DataFrame(
        [{"cluster_id": str(label), "rows": count} for label, count in sorted(result.cluster_sizes.items())]
    )
    st.plotly_chart(
        px.bar(sizes, x="cluster_id", y="rows", title="Cluster sizes — fitted K-Means labels"),
        use_container_width=True,
    )

    elbow = pd.DataFrame(result.elbow_points)
    st.plotly_chart(
        px.line(elbow, x="k", y="inertia", markers=True, title="Elbow diagnostic — standardized modeling space"),
        use_container_width=True,
    )
    st.caption("The elbow sweep is a diagnostic artifact, not multiple trials and not a guaranteed optimal-k selector.")

    projection = pd.DataFrame(result.pca_coordinates, columns=["PC1", "PC2"])
    projection["cluster_id"] = [str(value) for value in result.cluster_labels]
    st.plotly_chart(
        px.scatter(
            projection,
            x="PC1",
            y="PC2",
            color="cluster_id",
            title="PCA display projection — visualization only",
        ),
        use_container_width=True,
    )
    variance = sum(result.pca_explained_variance)
    st.caption(
        f"PCA is display-only ({variance:.1%} variance shown). Clustering and silhouette use the full standardized feature space."
    )

    with st.expander("Experiment details"):
        st.json(json.loads(result.experiment.config_json))
        st.write(f"Experiment ID: `{result.experiment.id}`")
        st.write(f"Selected trial count: **{len(result.experiment.trials)}**")
        st.json(result.artifact_paths)
