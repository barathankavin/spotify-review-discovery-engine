"""Segments tab — inferred (not verified) text-derived segment cuts."""

from __future__ import annotations

from collections import Counter

import altair as alt
import pandas as pd
import streamlit as st

from src.dashboard.constants import SEGMENT_DISCLAIMER
from src.dashboard.data_loader import DashboardData
from src.dashboard.style import SPOTIFY_GREEN, render_html

_AXIS = alt.Axis(labelColor="#B3B3B3", titleColor="#FFFFFF", gridColor="#222222",
                 tickColor="#333333", labelLimit=1000, labelFontSize=11)

_LABELS = {
    "mentions_premium": "Mentions premium / subscription",
    "mentions_ads": "Mentions ads",
    "mentions_free": "Affordability / free tier",
    "rating_negative": "Negative rating (1–2★)",
    "rating_neutral": "Neutral rating (3★)",
    "rating_positive": "Positive rating (4–5★)",
}


def _counts(segments: list[dict]) -> pd.DataFrame:
    counts = Counter(s.get("inferred_segment", "unknown") for s in segments)
    rows = [{"Segment": _LABELS.get(k, k), "Reviews": v} for k, v in counts.most_common()]
    return pd.DataFrame(rows)


def _theme_counts(theme: dict, data: DashboardData) -> pd.DataFrame:
    counts: Counter[str] = Counter()
    for rid in theme.get("supporting_review_ids", []):
        seg = data.segments_by_review.get(rid)
        if seg:
            counts[seg.get("inferred_segment", "unknown")] += 1
    rows = [{"Segment": _LABELS.get(k, k), "Reviews": v} for k, v in counts.most_common()]
    return pd.DataFrame(rows)


def _bar(df: pd.DataFrame, height: int = 240):
    return (
        alt.Chart(df)
        .mark_bar(color=SPOTIFY_GREEN, cornerRadiusEnd=4)
        .encode(
            x=alt.X("Reviews:Q", title="Reviews", axis=_AXIS),
            y=alt.Y("Segment:N", sort="-x", title=None, axis=_AXIS),
            tooltip=["Segment", "Reviews"],
        )
        .properties(height=height, background="transparent")
        .configure_view(strokeWidth=0)
    )


def render_segments(data: DashboardData) -> None:
    render_html('<div class="rd-section-title">Inferred segments</div>'
                '<div class="rd-section-sub">Behavioral cuts derived from review text signals.</div>')
    render_html(f'<div class="rd-card" style="border-left:3px solid #1DB954;background:#13211a;">'
                f'<div class="rd-card-desc" style="margin:0;color:#9fe3b5;">ℹ&nbsp; {SEGMENT_DISCLAIMER}</div></div>')

    render_html('<div class="rd-section-title" style="font-size:1.02rem;margin-top:.6rem;">'
                'Corpus-wide segment distribution</div>')
    seg_df = _counts(data.segments)
    if seg_df.empty:
        st.info("No segment data available.")
    else:
        st.altair_chart(_bar(seg_df), use_container_width=True)

    if data.themes:
        render_html('<div class="rd-section-title" style="font-size:1.02rem;margin-top:.6rem;">'
                    'Segments within a theme</div>')
        labels = [t.get("label", t.get("theme_id", "")) for t in data.themes]
        selected = st.selectbox("Filter by theme", labels, key="segment_theme_select")
        theme = next(t for t in data.themes if t.get("label") == selected)
        tdf = _theme_counts(theme, data)
        if tdf.empty:
            st.info("No segments for this theme's reviews.")
        else:
            st.altair_chart(_bar(tdf, height=200), use_container_width=True)
