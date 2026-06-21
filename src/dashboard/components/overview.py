"""Overview tab — theme distribution, trends, run metadata."""

from __future__ import annotations

from collections import defaultdict

import pandas as pd
import streamlit as st

from src.analysis.tags import iso_week
from src.dashboard.constants import ANOMALY_Z_THRESHOLD
from src.dashboard.data_loader import DashboardData


def _weekly_volume(reviews) -> pd.DataFrame:
    counts: dict[str, int] = defaultdict(int)
    ratings: dict[str, list[int]] = defaultdict(list)
    for review in reviews:
        week = iso_week(review.date)
        counts[week] += 1
        ratings[week].append(review.rating)
    rows = []
    for week in sorted(counts):
        rs = ratings[week]
        rows.append(
            {
                "week": week,
                "volume": counts[week],
                "avg_rating": round(sum(rs) / len(rs), 2),
            }
        )
    return pd.DataFrame(rows)


def _anomaly_weeks(df: pd.DataFrame) -> set[str]:
    if len(df) < 3:
        return set()
    mean = df["volume"].mean()
    std = df["volume"].std()
    if std == 0:
        return set()
    flagged = df[df["volume"] > mean + ANOMALY_Z_THRESHOLD * std]
    return set(flagged["week"].tolist())


def render_overview(data: DashboardData) -> None:
    st.subheader("Overview")

    meta = data.run_metadata
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Themes", len(data.themes))
    c2.metric("Sample size", meta.get("sample_size", "—"))
    c3.metric("Corpus reviews", len(data.reviews))
    c4.metric("Model", meta.get("model_id", "—")[:24])

    st.caption(
        f"Run ID: {meta.get('run_id', '—')}  ·  "
        f"Prompt: {meta.get('prompt_version', '—')}"
    )

    st.markdown("#### Theme distribution (sample)")
    theme_rows = [
        {
            "theme": t.get("label", t.get("theme_id", "")),
            "reviews": len(t.get("supporting_review_ids", [])),
        }
        for t in data.themes
    ]
    theme_df = pd.DataFrame(theme_rows).set_index("theme")
    st.bar_chart(theme_df)

    st.markdown("#### Corpus sentiment & volume by week")
    weekly = _weekly_volume(data.reviews)
    if weekly.empty:
        st.warning("No weekly trend data available.")
        return

    anomalies = _anomaly_weeks(weekly)
    if anomalies:
        st.warning(
            "Anomaly weeks (volume spike): "
            + ", ".join(sorted(anomalies))
        )

    chart_df = weekly.set_index("week")[["avg_rating", "volume"]]
    st.line_chart(chart_df)

    with st.expander("Run metadata (JSON)"):
        st.json(meta)
