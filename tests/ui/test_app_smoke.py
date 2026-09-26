"""Streamlit AppTest smoke tests for app launch and navigation."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_launch_smoke(tmp_storage_dir: Path) -> None:
    """Verify that app.py initializes and renders the Home page without errors."""
    app_path = Path(__file__).parent.parent.parent / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=15.0).run()

    # Verify no unhandled exception occurred
    assert not at.exception

    # Check top title and sidebar elements
    assert any("Welcome to DataMind" in str(title.value) for title in at.title)

    # Check that navigation radio options exist
    radios = at.radio
    assert len(radios) > 0
    assert "Home" in radios[0].options
    assert "Datasets" in radios[0].options


def test_datasets_page_render(tmp_storage_dir: Path) -> None:
    """Verify that navigating to the Datasets page renders cleanly."""
    app_path = Path(__file__).parent.parent.parent / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=15.0).run()
    assert not at.exception

    # Select Datasets page
    at.radio[0].set_value("Datasets").run()
    assert not at.exception
    assert any("Dataset Workspace" in str(title.value) for title in at.title)


def test_explore_page_render(tmp_storage_dir: Path) -> None:
    """Verify that navigating to the Explore page renders cleanly."""
    app_path = Path(__file__).parent.parent.parent / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=15.0).run()
    assert not at.exception

    # Select Explore page
    at.radio[0].set_value("Explore").run()
    assert not at.exception
    assert any("Exploratory Data Analysis" in str(title.value) for title in at.title)


def test_experiments_page_render(tmp_storage_dir: Path) -> None:
    """Verify that navigating to the Experiment page renders cleanly."""
    app_path = Path(__file__).parent.parent.parent / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=15.0).run()
    assert not at.exception

    # Select Experiment page
    at.radio[0].set_value("Experiment").run()
    assert not at.exception
    assert any("Supervised Experiments" in str(title.value) for title in at.title)


def test_home_shows_workspace_onboarding(tmp_storage_dir: Path) -> None:
    """Verify that the empty workspace shows truthful next-step guidance."""
    app_path = Path(__file__).parent.parent.parent / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=15.0).run()

    assert not at.exception
    assert any("New Project" in str(item.value) for item in at.subheader)
    assert any("Create or select a project" in str(item.value) for item in at.info)


def test_dataset_workspace_empty_state(tmp_storage_dir: Path) -> None:
    """Verify that the dataset page keeps project prerequisite guidance visible."""
    app_path = Path(__file__).parent.parent.parent / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=15.0).run()

    at.radio[0].set_value("Datasets").run()

    assert not at.exception
    assert any("No Active Project Selected" in str(item.value) for item in at.warning)


def test_home_quick_start_demo_button_loads_dataset(tmp_storage_dir: Path, migrated_db: Path) -> None:
    """Regression: Home quick-start buttons must load a demo dataset, not fail on wrong load_demo kwargs."""
    from datamind.services.datasets import DatasetService
    from datamind.services.projects import ProjectService

    project = ProjectService().create_project("Quick Start Lab", "")

    app_path = Path(__file__).parent.parent.parent / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=30.0)
    at.session_state["active_project_id"] = project.id
    at.run()
    assert not at.exception

    demo_button = next(b for b in at.button if b.label == "Iris Classification Demo")
    demo_button.click()
    at.run()

    assert not at.exception
    assert at.session_state["active_dataset_id"] is not None
    assert len(DatasetService().list_datasets(project.id)) == 1


def test_experiment_page_run_routes_numeric_features(tmp_storage_dir: Path, migrated_db: Path) -> None:
    """Regression: the Experiment page must route numeric columns to the numeric pipeline.

    The page compared ColumnSchema.inferred_type (a raw pandas dtype string such
    as "float64") against the literal "numeric", which classified every feature
    as categorical and made the categorical imputer crash during CV. This test
    drives the real form so the routing is covered end to end.
    """
    from datamind.contracts import DemoDatasetKind
    from datamind.services.datasets import DatasetService
    from datamind.services.projects import ProjectService

    project = ProjectService().create_project("UI Run Lab", "UI experiment run regression")
    DatasetService().load_demo(project.id, DemoDatasetKind.IRIS)

    app_path = Path(__file__).parent.parent.parent / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=120.0).run()
    at.session_state["active_project_id"] = project.id
    at.radio[0].set_value("Experiment").run()
    assert not at.exception

    run_button = next(
        b for b in at.button if "Run Supervised Cross-Validation Experiment" in b.label
    )
    run_button.click()
    at.run()

    assert not at.exception
    success_values = [str(item.value) for item in at.success]
    assert any("Experiment completed! Champion:" in v for v in success_values)
    latest = at.session_state["latest_experiment"]
    assert latest.status == "completed"
    assert latest.selected_trial_id is not None
    assert any("Cross-Validation Results" in str(item.value) for item in at.subheader)


