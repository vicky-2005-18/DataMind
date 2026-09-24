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
    assert any("From raw data to defensible results" in str(item.value) for item in at.subheader)
    assert any("Create or select a project" in str(item.value) for item in at.info)


def test_dataset_workspace_empty_state(tmp_storage_dir: Path) -> None:
    """Verify that the dataset page keeps project prerequisite guidance visible."""
    app_path = Path(__file__).parent.parent.parent / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=15.0).run()

    at.radio[0].set_value("Datasets").run()

    assert not at.exception
    assert any("No Active Project Selected" in str(item.value) for item in at.warning)


