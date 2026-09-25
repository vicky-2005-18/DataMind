"""Datasets page: CSV file upload, offline demo loaders, profiling, and role suggestions."""

from __future__ import annotations

import streamlit as st

from datamind.config import get_settings
from datamind.contracts import DatasetSummary, DemoDatasetKind, ServiceError
from datamind.services.datasets import DatasetService
from datamind.ui.components import (
    pill_html,
    render_active_project_banner,
    render_bento_grid,
    render_header,
    render_hero_stats,
    render_service_error,
    render_workflow_stepper,
)
from datamind.ui.navigation import NavigationContext

DEMO_DESCRIPTIONS = {
    DemoDatasetKind.IRIS: "Iris Flower Classification (150 rows, 4 numeric features, 3 classes)",
    DemoDatasetKind.SYNTHETIC_REGRESSION: "Synthetic Regression (500 rows, 6 numeric features, continuous target)",
    DemoDatasetKind.SYNTHETIC_BLOBS: "Synthetic 4D Blobs Clustering (600 rows, 4 numeric features, 3 clusters)",
}


def render_datasets_page() -> None:
    """Render the Datasets workspace page."""
    render_header(
        title="Dataset Workspace",
        subtitle="Import tabular CSV datasets, load offline demos, and inspect structural quality profiles",
    )
    render_workflow_stepper("Prepare")

    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)

    if not active_project:
        return

    service = DatasetService()
    settings = get_settings()
    project_datasets = service.list_datasets(active_project.id)

    if project_datasets:
        current_active_id = st.session_state.get("active_dataset_id")
        ds_dict = {
            dataset.id: (
                f"{dataset.display_name} · {dataset.row_count:,} rows · "
                f"{dataset.column_count} columns"
            )
            for dataset in project_datasets
        }
        selected_idx = (
            list(ds_dict.keys()).index(current_active_id)
            if current_active_id in ds_dict
            else 0
        )
        chosen_id = st.selectbox(
            "Active dataset",
            options=list(ds_dict.keys()),
            index=selected_idx,
            format_func=lambda dataset_id: ds_dict[dataset_id],
            help="This dataset is used by Explore, Experiment, and Clustering.",
        )
        if NavigationContext.set_active_dataset(chosen_id):
            st.rerun()
    else:
        st.info("No datasets yet. Import a CSV or load an offline demo to begin.")

    # Track active/viewed dataset in session state
    if "active_dataset_id" not in st.session_state:
        st.session_state["active_dataset_id"] = None

    tab_upload, tab_demos, tab_manage = st.tabs(
        ["Upload CSV", "Load Demo Dataset", "Existing Project Datasets"]
    )

    # 1. TAB: Upload CSV
    with tab_upload:
        st.subheader("Upload a Tabular CSV")
        st.caption(
            f"Supports UTF-8 and UTF-8-BOM CSVs up to {settings.max_upload_mib} MiB, "
            f"{settings.max_rows:,} rows, and {settings.max_columns} columns."
        )

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
                    NavigationContext.set_active_dataset(new_ds.id)
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
            kind: description for kind, description in DEMO_DESCRIPTIONS.items()
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
                NavigationContext.set_active_dataset(demo_ds.id)
                st.success(f"Demo **{demo_ds.display_name}** loaded successfully!")
                st.rerun()
            except ServiceError as err:
                render_service_error(err)
            except Exception as exc:
                st.error(f"Failed to generate demo: {exc}")

    with tab_manage:
        st.subheader("Datasets in this Project")
        if not project_datasets:
            st.info("No datasets loaded in this project yet. Upload a CSV or load a demo dataset.")
        else:
            dataset_rows = [
                {
                    "Dataset": dataset.display_name,
                    "Rows": dataset.row_count,
                    "Columns": dataset.column_count,
                    "Source": dataset.source_kind.title(),
                    "Created": dataset.created_at[:10],
                }
                for dataset in project_datasets
            ]
            st.dataframe(dataset_rows, width='stretch', hide_index=True)
            st.caption("Use the Active dataset selector above to inspect or work with a dataset.")

    # RENDER PROFILE VIEW IF A DATASET IS ACTIVE
    active_dataset_id = st.session_state.get("active_dataset_id")
    if active_dataset_id:
        selected_dataset = service.get_dataset(active_dataset_id)
        if selected_dataset:
            st.divider()
            render_dataset_inspection(selected_dataset, service)


def render_dataset_inspection(dataset: DatasetSummary, service: DatasetService) -> None:
    """Render structural metrics, quality warnings, role suggestions, and data preview."""
    st.subheader(f"Dataset Profile: {dataset.display_name}")
    st.caption(
        f"{dataset.source_kind.title()} source · Created "
        f"{dataset.created_at[:19].replace('T', ' ')} UTC"
    )
    with st.expander("Dataset details"):
        st.code(
            f"Dataset ID: {dataset.id}\n"
            f"SHA-256: {dataset.raw_sha256}\n"
            f"Parser: {dataset.parser_version}"
        )

    profile = dataset.get_profile()

    # Health bento: structural stats, type distribution, missing cells, warnings
    role_counts: dict[str, int] = {}
    for col in profile.columns:
        role_counts[col.suggested_role.value] = role_counts.get(col.suggested_role.value, 0) + 1
    role_variants = {
        "numeric": "cyan",
        "categorical": "primary",
        "id_like": "muted",
        "constant": "amber",
        "unsupported": "rose",
    }
    type_pills = " ".join(
        pill_html(f"{role.replace('_', '- ')} ({count})", role_variants.get(role, "muted"))
        for role, count in sorted(role_counts.items())
    )

    missing_cells = sum(col.null_count for col in profile.columns)
    total_cells = profile.row_count * profile.column_count
    if missing_cells > 0:
        missing_body = (
            f"{render_hero_stats([(f'{missing_cells:,}', 'Missing cells'), (f'{total_cells:,}', 'Total cells')])}"
            f"<p style='margin-top:0.55rem;'>{pill_html('Imputation required before training', 'amber')}</p>"
        )
    else:
        missing_body = (
            f"{render_hero_stats([('0', 'Missing cells'), (f'{total_cells:,}', 'Total cells')])}"
            f"<p style='margin-top:0.55rem;'>{pill_html('Complete matrix', 'success')}</p>"
        )

    if profile.quality_warnings:
        warning_body = (
            f"<p style='margin-top:0.35rem;'>{pill_html(f'{len(profile.quality_warnings)} warnings', 'amber')}</p>"
            "<p style='margin-top:0.55rem; font-size:0.85rem; color:var(--dm-text-muted);'>"
            "Review the expanded warnings list below before training.</p>"
        )
    else:
        warning_body = (
            f"<p style='margin-top:0.35rem;'>{pill_html('No warnings', 'success')}</p>"
            "<p style='margin-top:0.55rem; font-size:0.85rem; color:var(--dm-text-muted);'>"
            "Structural checks passed for this dataset.</p>"
        )

    render_bento_grid(
        [
            {
                "title": "Structural Profile",
                "kicker_html": pill_html("Schema", "cyan"),
                "body_html": render_hero_stats(
                    [
                        (f"{profile.row_count:,}", "Rows"),
                        (str(profile.column_count), "Columns"),
                        (f"{profile.memory_bytes / 1024:.1f}K", "Memory KB"),
                    ]
                ),
            },
            {
                "title": "Type Distribution",
                "kicker_html": pill_html("Inferred roles", "primary"),
                "body_html": f"<p style='margin-top:0.35rem; line-height:2;'>{type_pills}</p>",
            },
            {
                "title": "Missing Data",
                "kicker_html": pill_html("Cell health", "primary"),
                "body_html": missing_body,
            },
            {
                "title": "Quality Warnings",
                "kicker_html": pill_html("Hygiene", "primary"),
                "body_html": warning_body,
            },
        ]
    )

    # Duplicate rows metric kept visible below the bento row
    st.metric("Duplicate Rows", f"{profile.duplicate_row_count:,}")

    # Quality warnings callout
    if profile.quality_warnings:
        with st.expander(f"Quality Warnings ({len(profile.quality_warnings)})", expanded=True):
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
            "Missing Count": col.null_count,
            "Null %": col.null_percentage,
            "Unique Values": col.unique_count,
            "Sample Values": ", ".join(col.sample_values[:4]),
            "Column Warnings": "; ".join(col.warnings) if col.warnings else "None",
        })

    st.dataframe(
        col_data,
        width='stretch',
        hide_index=True,
        column_config={
            "Null %": st.column_config.ProgressColumn(
                "Null %",
                help="Share of missing cells in this column",
                min_value=0.0,
                max_value=100.0,
                format="%.2f%%",
            ),
        },
    )

    # Data Preview
    st.markdown("### Raw Table Preview")
    st.caption("First 10 rows loaded from immutable storage with verified SHA-256 integrity.")
    try:
        df = service.load_dataframe(dataset.id)
        st.dataframe(df.head(10), width='stretch')
    except Exception as exc:
        st.error(f"Could not preview stored table: {exc}")
