"""Streamlit dashboard — Spotify Review Discovery Engine (Phase 4 + 5)."""

from __future__ import annotations

import streamlit as st

from src.dashboard.bootstrap import apply_streamlit_secrets
from src.dashboard.components.chatbot import render_chat_panel
from src.dashboard.components.header import render_header
from src.dashboard.components.overview import render_overview
from src.dashboard.components.review_discovery import render_review_discovery
from src.dashboard.components.segments import render_segments
from src.dashboard.components.themes import render_theme_cards, render_theme_deepdive
from src.dashboard.components.unmet_needs import render_unmet_needs
from src.dashboard.constants import APP_TITLE
from src.dashboard.data_loader import load_dashboard_data
from src.dashboard.pipeline_status import get_pipeline_status
from src.dashboard.style import inject_global_css

apply_streamlit_secrets(st)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data(show_spinner="Loading artifacts…")
def _load_data():
    return load_dashboard_data()


def main() -> None:
    inject_global_css()
    render_header(get_pipeline_status())

    try:
        data = _load_data()
    except (FileNotFoundError, ValueError) as exc:
        st.error(str(exc))
        st.stop()

    if data.using_lkg:
        st.warning("Showing **last-known-good** artifacts — the latest run failed validation.")
    for warning in data.load_warnings:
        st.warning(warning)

    tab_overview, tab_themes, tab_segments, tab_unmet, tab_reviews = st.tabs(
        ["Overview", "Themes & Chat", "Segments", "Unmet Needs", "Review Discovery"]
    )

    with tab_overview:
        render_overview(data)

    with tab_themes:
        left, right = st.columns([1.1, 1], gap="large")
        with left:
            render_theme_cards(data)
        with right:
            render_chat_panel()
        render_theme_deepdive(data)

    with tab_segments:
        render_segments(data)

    with tab_unmet:
        render_unmet_needs(data)

    with tab_reviews:
        render_review_discovery(data)


if __name__ == "__main__":
    main()
