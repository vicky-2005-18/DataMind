"""T39 dataset and project transition invalidation."""

from __future__ import annotations

import streamlit as st

from datamind.ui.navigation import NavigationContext


def test_t39_dataset_change_invalidates_dependent_draft():
    st.session_state.clear()
    st.session_state["active_dataset_id"] = "dataset-a"
    st.session_state["explore_target_choice"] = "species"
    st.session_state["explore_numeric_features"] = ["x"]
    st.session_state["exp_target"] = "species"
    st.session_state["latest_experiment"] = object()
    st.session_state["view_old"] = object()
    st.session_state["split_old"] = object()

    assert NavigationContext.set_active_dataset("dataset-b") is True
    assert st.session_state["active_dataset_id"] == "dataset-b"
    for key in (
        "explore_target_choice",
        "explore_numeric_features",
        "exp_target",
        "latest_experiment",
        "view_old",
        "split_old",
    ):
        assert key not in st.session_state
    assert NavigationContext.set_active_dataset("dataset-b") is False
