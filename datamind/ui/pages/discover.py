"""Algorithm cards and real seeded educational playgrounds."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly import express as px

from datamind.services.playground import (
    run_classification_playground,
    run_clustering_playground,
)
from datamind.ui.components import (
    render_active_project_banner,
    render_header,
    render_service_error,
    render_workflow_stepper,
    style_plotly_figure,
)
from datamind.ui.navigation import NavigationContext

ALGORITHM_CARDS = [
    {
        "name": "Decision Tree",
        "family": "Classification",
        "intuition": "Repeatedly splits features into regions that make labels more homogeneous.",
        "useful": "Readable nonlinear rules and mixed feature interactions.",
        "limitation": "Deep trees can overfit small changes and noise.",
        "scaling": "Scaling usually does not change tree splits.",
        "parameters": "Maximum depth, minimum leaf size",
    },
    {
        "name": "k-Nearest Neighbors",
        "family": "Classification",
        "intuition": "Predicts from the labels of nearby fitted examples.",
        "useful": "Flexible local boundaries on modest-sized datasets.",
        "limitation": "Distance can weaken in high dimensions.",
        "scaling": "Scaling is important because features define distance.",
        "parameters": "Neighbor count k, voting weights",
    },
    {
        "name": "K-Means",
        "family": "Clustering",
        "intuition": "Alternates assignment to centroids and centroid updates.",
        "useful": "Exploring compact numeric groups without a target.",
        "limitation": "Requires a chosen k and favors roughly spherical groups.",
        "scaling": "Standardization prevents large-unit features dominating distance.",
        "parameters": "Cluster count k, initialization seed",
    },
]


def render_discover_page() -> None:
    """Render reviewed cards and fitted synthetic playgrounds."""
    render_header(
        title="Algorithm Discovery & Educational Playground",
        subtitle="Inspect algorithm assumptions and run real seeded two-dimensional models",
    )
    render_workflow_stepper("Learn")
    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)

    card_tab, playground_tab = st.tabs(["Algorithm cards", "Interactive playground"])
    with card_tab:
        families = sorted({card["family"] for card in ALGORITHM_CARDS})
        family = st.selectbox("Algorithm family", ["All", *families])
        visible = [card for card in ALGORITHM_CARDS if family == "All" or card["family"] == family]
        for card in visible:
            with st.container(border=True):
                st.subheader(card["name"])
                st.caption(card["family"])
                st.write(card["intuition"])
                st.write(f"**Useful when:** {card['useful']}")
                st.write(f"**Limitation:** {card['limitation']}")
                st.write(f"**Scaling:** {card['scaling']}")
                st.write(f"**Exposed controls:** {card['parameters']}")

    with playground_tab:
        kind = st.selectbox("Playground", ["Decision Tree", "k-Nearest Neighbors", "K-Means"])
        with st.form("playground_form"):
            sample_count = st.slider("Synthetic sample count", 100, 1000, 300, 50)
            seed = st.number_input("Synthetic seed", min_value=0, max_value=2_147_483_647, value=42)
            if kind in {"Decision Tree", "k-Nearest Neighbors"}:
                noise = st.slider("Moons noise", 0.0, 0.5, 0.25, 0.05)
            else:
                noise = st.slider("Blob spread", 0.1, 3.0, 1.0, 0.1)
            tree_depth = st.slider("Maximum tree depth", 1, 20, 3)
            neighbors = st.slider("Neighbor count k", 1, 25, 5)
            cluster_count = st.slider("Cluster count k", 2, 10, 3)
            submitted = st.form_submit_button("Run playground", type="primary")

        if submitted:
            try:
                if kind == "Decision Tree":
                    result = run_classification_playground(
                        "decision_tree",
                        sample_count=sample_count,
                        noise=noise,
                        seed=int(seed),
                        tree_depth=tree_depth,
                    )
                elif kind == "k-Nearest Neighbors":
                    result = run_classification_playground(
                        "knn",
                        sample_count=sample_count,
                        noise=noise,
                        seed=int(seed),
                        n_neighbors=neighbors,
                    )
                else:
                    result = run_clustering_playground(
                        sample_count=sample_count,
                        cluster_count=cluster_count,
                        noise=noise,
                        seed=int(seed),
                    )
                st.session_state["playground_result"] = result
            except Exception as exc:
                render_service_error(exc)

        result = st.session_state.get("playground_result")
        if result is None:
            st.info("Choose controls and click Run playground. Widget changes alone do not fit a model.")
            return

        points = pd.DataFrame(result.points, columns=["x", "y"])
        points["label"] = [str(value) for value in result.labels]
        if result.mesh_x is not None and result.mesh_y is not None and result.mesh_values is not None:
            figure = go.Figure(
                data=go.Contour(
                    x=result.mesh_x[0],
                    y=[row[0] for row in result.mesh_y],
                    z=result.mesh_values,
                    showscale=False,
                    opacity=0.35,
                    contours={"coloring": "fill"},
                )
            )
            for label in sorted(points["label"].unique()):
                subset = points[points["label"] == label]
                figure.add_scatter(x=subset["x"], y=subset["y"], mode="markers", name=f"Class {label}")
            figure.update_layout(title=f"Synthetic playground — {result.kind}")
            figure = style_plotly_figure(figure)
        else:
            figure = px.scatter(
                points,
                x="x",
                y="y",
                color="label",
                title="Synthetic playground — fitted K-Means assignments",
            )
            figure = style_plotly_figure(figure)
        st.plotly_chart(figure, width='stretch')
        st.write(result.explanation)
        st.warning(result.limitation)
        st.caption(f"Synthetic demonstration only • seed {result.seed} • parameters {result.parameters}")
