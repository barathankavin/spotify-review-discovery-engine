"""Streamlit dashboard — Phase 4 entry point."""

from __future__ import annotations

import streamlit as st

from src.dashboard.bootstrap import apply_streamlit_secrets
from src.dashboard.components.chatbot import render_chatbot
from src.dashboard.components.overview import render_overview
from src.dashboard.components.segments import render_segments
from src.dashboard.components.themes import render_themes
from src.dashboard.components.unmet_needs import render_unmet_needs
from src.dashboard.constants import APP_SUBTITLE, APP_TITLE
from src.dashboard.data_loader import load_dashboard_data

apply_streamlit_secrets(st)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner="Loading artifacts…")
def _load_data():
    return load_dashboard_data()


def main() -> None:
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)

    try:
        data = _load_data()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    if data.using_lkg:
        st.warning(
            "Showing **last-known-good** artifacts — the latest run failed validation."
        )
    for warning in data.load_warnings:
        st.warning(warning)

    tab_overview, tab_themes, tab_segments, tab_unmet, tab_chat = st.tabs(
        ["Overview", "Theme Deep-Dive", "Segments", "Unmet Needs", "Chatbot"]
    )

    with tab_overview:
        render_overview(data)

    with tab_themes:
        render_themes(data)

    with tab_segments:
        render_segments(data)

    with tab_unmet:
        render_unmet_needs(data)

    with tab_chat:
        render_chatbot()


if __name__ == "__main__":
    main()
