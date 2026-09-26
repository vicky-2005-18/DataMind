"""Regression: programmatic project activation must survive the sidebar selectbox rerun sync."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from datamind.services.projects import ProjectService


def _run_app() -> AppTest:
    app_path = Path(__file__).parent.parent.parent / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=30.0).run()
    assert not at.exception
    return at


def test_create_and_select_activates_new_project(tmp_storage_dir: Path, migrated_db: Path) -> None:
    ProjectService().create_project("Existing Lab", "pre-existing project")

    at = _run_app()
    at.text_input[0].set_value("Fresh Lab")
    submit = next(b for b in at.button if b.label == "Create & Select")
    submit.click()
    at.run()

    assert not at.exception
    fresh = next(p for p in ProjectService().list_projects() if p.name == "Fresh Lab")
    assert at.session_state["active_project_id"] == fresh.id
    assert at.session_state["sidebar_project_select"] == fresh.id


def test_activate_button_switches_project(tmp_storage_dir: Path, migrated_db: Path) -> None:
    first = ProjectService().create_project("First Lab", "")
    second = ProjectService().create_project("Second Lab", "")

    at = _run_app()
    active_id = at.session_state["active_project_id"]
    target = second if second.id != active_id else first

    activate = next(b for b in at.button if b.key == f"sel_proj_{target.id}")
    activate.click()
    at.run()

    assert not at.exception
    assert at.session_state["active_project_id"] == target.id
    assert at.session_state["sidebar_project_select"] == target.id
