"""Theme Deep-Dive tab."""

from __future__ import annotations

from collections import Counter

import pandas as pd
import streamlit as st

from src.analysis.tags import iso_week
from src.dashboard.constants import MAX_SUMMARY_WORDS
from src.dashboard.data_loader import DashboardData


def _render_quote(text: str) -> None:
    quoted = "\n".join(f"> {line}" if line else ">" for line in text.splitlines())
    st.markdown(quoted)


def _truncate_summary(text: str, max_words: int = MAX_SUMMARY_WORDS) -> tuple[str, bool]:
    words = text.split()
    if len(words) <= max_words:
        return text, False
    return " ".join(words[:max_words]) + " …", True


def _theme_weekly_counts(theme: dict, data: DashboardData) -> pd.DataFrame:
    counts: Counter[str] = Counter()
    for rid in theme.get("supporting_review_ids", []):
        review = data.reviews_by_id.get(rid)
        if review:
            counts[iso_week(review.date)] += 1
    if not counts:
        return pd.DataFrame(columns=["week", "count"])
    rows = [{"week": w, "count": counts[w]} for w in sorted(counts)]
    return pd.DataFrame(rows).set_index("week")


def _theme_segment_breakdown(theme: dict, data: DashboardData) -> pd.DataFrame:
    seg_counts: Counter[str] = Counter()
    for rid in theme.get("supporting_review_ids", []):
        seg = data.segments_by_review.get(rid)
        if seg:
            seg_counts[seg.get("inferred_segment", "unknown")] += 1
    if not seg_counts:
        return pd.DataFrame(columns=["segment", "count"])
    return pd.DataFrame(
        [{"segment": k, "count": v} for k, v in seg_counts.most_common()]
    ).set_index("segment")


def render_themes(data: DashboardData) -> None:
    st.subheader("Theme Deep-Dive")

    if not data.themes:
        st.warning("No themes in artifacts.")
        return

    labels = [t.get("label", t.get("theme_id", "")) for t in data.themes]
    selected = st.selectbox("Select theme", labels, key="theme_select")
    theme = next(t for t in data.themes if t.get("label") == selected)

    st.markdown(f"**{theme.get('label')}**")
    if theme.get("description"):
        st.caption(theme["description"])

    summary = theme.get("summary", "")
    display_summary, truncated = _truncate_summary(summary)
    st.markdown("#### Summary")
    st.write(display_summary)
    if truncated:
        st.caption(f"Summary truncated to {MAX_SUMMARY_WORDS} words for display.")

    word_count = len(display_summary.split())
    st.caption(f"Word count: {word_count}")

    st.markdown("#### Supporting quotes")
    quotes = theme.get("quotes", [])
    if not quotes:
        st.info("No quotes attached to this theme.")
    for quote in quotes:
        rid = quote.get("review_id", "")
        text = quote.get("text", "")
        _render_quote(text)
        st.caption(f"review_id: `{rid}`")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Frequency by week")
        week_df = _theme_weekly_counts(theme, data)
        if week_df.empty:
            st.info("No dated reviews for this theme.")
        else:
            st.line_chart(week_df)

    with col2:
        st.markdown("#### Segment breakdown")
        seg_df = _theme_segment_breakdown(theme, data)
        if seg_df.empty:
            st.info("No segment data for this theme.")
        else:
            st.bar_chart(seg_df)

    st.caption(
        f"{len(theme.get('supporting_review_ids', []))} supporting reviews in sample"
    )
