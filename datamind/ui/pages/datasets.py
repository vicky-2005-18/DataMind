"""Datasets page: CSV file upload, offline demo loaders, profiling, and role suggestions."""

from __future__ import annotations

import streamlit as st

from datamind.contracts import DatasetSummary, DemoDatasetKind, ServiceError
from datamind.services.datasets import DatasetService
from datamind.ui.components import (
    render_active_project_banner,
    render_header,
    render_service_error,
)
from datamind.ui.navigation import NavigationContext


def render_datasets_page() -> None:
    """Render the Datasets workspace page."""
    render_header(
        title="Dataset Workspace",
        subtitle="Import tabular CSV datasets, load offline demos, and inspect structural quality profiles",
    )

    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)

    if not active_project:
        return

    service = DatasetService()

    # Track active/viewed dataset in session state
    if "active_dataset_id" not in st.session_state:
        st.session_state["active_dataset_id"] = None

    tab_upload, tab_demos, tab_manage = st.tabs(
        ["📤 Upload CSV", "🧪 Load Demo Dataset", "📚 Existing Project Datasets"]
    )

    # 1. TAB: Upload CSV
    with tab_upload:
        st.subheader("Upload a Tabular CSV")
        st.caption("Supports UTF-8 and UTF-8-BOM encoded CSVs up to 10 MiB, 20,000 rows, and 100 columns.")

        uploaded_file = st.file_uploader(
            "Select CSV file",
            type=["csv"],
            key="csv_uploader",
            help="Upload a standard comma-delimited tabular CSV.",
        )

        display_name_default = uploaded_file.name if uploaded_file else ""
        custom_name = st.text_input(
            "Dataset Display Name",
            value=display_name_default,
            placeholder="e.g. Customer Churn Q3",
            help="A human-readable label for this dataset.",
        )

        if st.button("Validate & Ingest Dataset", type="primary", disabled=uploaded_file is None):
            if uploaded_file is not None:
                try:
                    file_bytes = uploaded_file.getvalue()
                    ds_name = custom_name.strip() or uploaded_file.name
                    with st.spinner("Validating byte contracts, parsing, and profiling..."):
                        new_ds = service.import_csv(
                            project_id=active_project.id,
                            raw_bytes=file_bytes,
                            display_name=ds_name,
                        )
                    st.session_state["active_dataset_id"] = new_ds.id
                    st.success(f"Dataset **{new_ds.display_name}** ingested successfully! ({new_ds.row_count:,} rows, {new_ds.column_count} columns)")
                    st.rerun()
                except ServiceError as err:
                    render_service_error(err)
                except Exception as exc:
                    st.error(f"Unexpected error during import: {exc}")

    # 2. TAB: Load Demo Datasets
    with tab_demos:
        st.subheader("Offline Demo Datasets")
        st.caption("Load curated educational datasets generated completely offline without internet dependencies.")

        demo_options = {
            DemoDatasetKind.IRIS: "🌸 Iris Flower Classification (150 rows, 4 numeric features, 3 classes)",
            DemoDatasetKind.SYNTHETIC_REGRESSION: "📈 Synthetic Regression (200 rows, 4 numeric features, continuous target)",
            DemoDatasetKind.SYNTHETIC_BLOBS: "🫧 Synthetic 3D Blobs Clustering (300 rows, 3 numeric features, 3 clusters)",
        }

        selected_kind = st.selectbox(
            "Choose a demo dataset",
            options=list(demo_options.keys()),
            format_func=lambda k: demo_options[k],
        )

        seed = st.number_input(
            "Random Generation Seed",
            min_value=0,
            max_value=999999,
            value=42,
            step=1,
            help="Seed used for deterministic synthetic generation.",
        )

        if st.button("Load Demo into Project", type="primary"):
            try:
                with st.spinner("Generating demo and computing structural profile..."):
                    demo_ds = service.load_demo(
                        project_id=active_project.id,
                        demo_kind=selected_kind,
                        seed=int(seed),
                    )
                st.session_state["active_dataset_id"] = demo_ds.id
                st.success(f"Demo **{demo_ds.display_name}** loaded successfully!")
                st.rerun()
            except ServiceError as err:
                render_service_error(err)
            except Exception as exc:
                st.error(f"Failed to generate demo: {exc}")

    # 3. TAB: Existing Datasets
    with tab_manage:
        st.subheader("Datasets in this Project")
        project_datasets = service.list_datasets(active_project.id)

        if not project_datasets:
            st.info("No datasets loaded in this project yet. Upload a CSV or load a demo dataset.")
        else:
            ds_dict = {ds.id: f"{ds.display_name} ({ds.row_count:,} rows, {ds.column_count} cols) — {ds.created_at[:10]}" for ds in project_datasets}
            current_active_id = st.session_state.get("active_dataset_id")
            selected_idx = 0
            if current_active_id and current_active_id in ds_dict:
                selected_idx = list(ds_dict.keys()).index(current_active_id)

            chosen_id = st.selectbox(
                "Select dataset to inspect",
                options=list(ds_dict.keys()),
                index=selected_idx,
                format_func=lambda x: ds_dict[x],
            )
            if chosen_id != current_active_id:
                st.session_state["active_dataset_id"] = chosen_id
                st.rerun()

    # RENDER PROFILE VIEW IF A DATASET IS ACTIVE
    active_dataset_id = st.session_state.get("active_dataset_id")
    if active_dataset_id:
        selected_dataset = service.get_dataset(active_dataset_id)
        if selected_dataset:
            st.divider()
            render_dataset_inspection(selected_dataset, service)


def render_dataset_inspection(dataset: DatasetSummary, service: DatasetService) -> None:
    """Render structural metrics, quality warnings, role suggestions, and data preview."""
    st.subheader(f"📊 Dataset Profile: {dataset.display_name}")
    st.caption(f"Source: `{dataset.source_kind.upper()}` • Created: `{dataset.created_at[:19].replace('T', ' ')} UTC` • ID: `{dataset.id[:8]}` • SHA-256: `{dataset.raw_sha256[:12]}...`")

    profile = dataset.get_profile()

    # KPI summary metrics
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    mcol1.metric("Rows", f"{profile.row_count:,}")
    mcol2.metric("Columns", f"{profile.column_count:,}")
    mcol3.metric("Duplicate Rows", f"{profile.duplicate_row_count:,}")
    mcol4.metric("Memory Size", f"{profile.memory_bytes / 1024:.1f} KB")

    # Quality warnings callout
    if profile.quality_warnings:
        with st.expander(f"⚠️ Quality Warnings ({len(profile.quality_warnings)})", expanded=True):
            for w in profile.quality_warnings:
                st.warning(f"• {w}")

    # Columns & Role Suggestions
    st.markdown("### Feature Schema & Role Suggestions")
    st.caption("Review inferred types, null distributions, cardinality, and suggested ML roles.")

    col_data = []
    for col in profile.columns:
        col_data.append({
            "Column Name": col.name,
            "Inferred Type": col.dtype,
            "Suggested Role": col.suggested_role.value,
            "Missing Count": f"{col.null_count:,} ({col.null_percentage}%)",
            "Unique Values": f"{col.unique_count:,}",
            "Sample Values": ", ".join(col.sample_values[:4]),
            "Column Warnings": "; ".join(col.warnings) if col.warnings else "None",
        })

    st.dataframe(col_data, use_container_width=True, hide_index=True)

    # Data Preview
    st.markdown("### Raw Table Preview")
    st.caption("First 10 rows loaded from immutable storage with verified SHA-256 integrity.")
    try:
        df = service.load_dataframe(dataset.id)
        st.dataframe(df.head(10), use_container_width=True)
    except Exception as exc:
        st.error(f"Could not preview stored table: {exc}")
