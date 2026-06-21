"""Segments tab — inferred segment distribution."""

from __future__ import annotations

from collections import Counter

import pandas as pd
import streamlit as st

from src.dashboard.constants import SEGMENT_DISCLAIMER
from src.dashboard.data_loader import DashboardData


def _segment_counts(segments: list[dict]) -> pd.DataFrame:
    counts = Counter(s.get("inferred_segment", "unknown") for s in segments)
    rows = [{"segment": k, "count": v} for k, v in counts.most_common()]
    return pd.DataFrame(rows).set_index("segment")


def _theme_segment_counts(theme: dict, data: DashboardData) -> pd.DataFrame:
    counts: Counter[str] = Counter()
    for rid in theme.get("supporting_review_ids", []):
        seg = data.segments_by_review.get(rid)
        if seg:
            counts[seg.get("inferred_segment", "unknown")] += 1
    rows = [{"segment": k, "count": v} for k, v in counts.most_common()]
    if not rows:
        return pd.DataFrame(columns=["segment", "count"])
    return pd.DataFrame(rows).set_index("segment")


def render_segments(data: DashboardData) -> None:
    st.subheader("Segments")

    st.warning(SEGMENT_DISCLAIMER)

    st.markdown("#### Sample-wide segment distribution")
    seg_df = _segment_counts(data.segments)
    if seg_df.empty:
        st.info("No segment data available.")
    else:
        st.bar_chart(seg_df)

    st.markdown("#### Per-theme segment cuts")
    theme_labels = [t.get("label", t.get("theme_id", "")) for t in data.themes]
    if not theme_labels:
        st.info("No themes to cross-tabulate.")
        return

    selected = st.selectbox("Filter by theme", theme_labels, key="segment_theme_select")
    theme = next(t for t in data.themes if t.get("label") == selected)
    theme_seg = _theme_segment_counts(theme, data)
    if theme_seg.empty:
        st.info("No segments for this theme's reviews.")
    else:
        st.bar_chart(theme_seg)

    with st.expander("Segment field reference"):
        st.markdown(
            "- **mentions_premium** — review text references premium/subscription\n"
            "- **mentions_ads** — review mentions ads\n"
            "- **mentions_free** — affordability / free-tier language\n"
            "- **rating_negative / neutral / positive** — fallback from star rating"
        )
