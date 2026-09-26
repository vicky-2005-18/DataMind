"""DataMind: An Interactive Machine Learning Discovery & Experimentation Platform.

Main Streamlit application entry point.
"""

from __future__ import annotations

import streamlit as st

from datamind.config import get_settings
from datamind.storage.database import run_migrations
from datamind.ui.components import apply_global_styles
from datamind.ui.navigation import NavigationContext, render_sidebar
from datamind.ui.pages.clustering import render_clustering_page
from datamind.ui.pages.compare import render_compare_page
from datamind.ui.pages.datasets import render_datasets_page
from datamind.ui.pages.discover import render_discover_page
from datamind.ui.pages.experiments import render_experiments_page
from datamind.ui.pages.explain_export import render_explain_export_page
from datamind.ui.pages.explore import render_explore_page
from datamind.ui.pages.home import render_home_page
from datamind.ui.pages.predict import render_predict_page
from datamind.ui.theme import Theme

# Set top-level page configuration
st.set_page_config(
    page_title="DataMind — Interactive ML Lab",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def bootstrap_application() -> None:
    """Initialize configuration, storage directories, and database migrations."""
    settings = get_settings()
    settings.ensure_directories()
    # Idempotently run any pending SQLite migrations
    run_migrations(settings.db_path)
    NavigationContext.initialize()


def main() -> None:
    """Main application execution router."""
    bootstrap_application()
    apply_global_styles()
    # Apply theme CSS variables
    st.markdown(Theme.get_css_variables(), unsafe_allow_html=True)

    pages = {
        "Home": render_home_page,
        "Datasets": render_datasets_page,
        "Explore": render_explore_page,
        "Experiment": render_experiments_page,
        "Compare": render_compare_page,
        "Predict": render_predict_page,
        "Explain & Export": render_explain_export_page,
        "Clustering": render_clustering_page,
        "Discover": render_discover_page,
    }

    selected_page = render_sidebar(pages)

    # Render selected page
    render_fn = pages.get(selected_page, render_home_page)
    render_fn()


if __name__ == "__main__":
    main()
