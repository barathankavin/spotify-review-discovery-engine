"""Overview tab — pipeline pulse, theme distribution, weekly trend, anomalies."""

from __future__ import annotations

from collections import defaultdict

import altair as alt
import pandas as pd
import streamlit as st

from src.analysis.tags import iso_week
from src.dashboard.constants import ANOMALY_Z_THRESHOLD
from src.dashboard.data_loader import DashboardData
from src.dashboard.style import SPOTIFY_GREEN, render_html

_AXIS = alt.Axis(labelColor="#B3B3B3", titleColor="#FFFFFF", gridColor="#222222", tickColor="#333333")


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
                "Review volume": counts[week],
                "Average rating": round(sum(rs) / len(rs), 2),
            }
        )
    return pd.DataFrame(rows)


def _anomaly_weeks(df: pd.DataFrame) -> set[str]:
    if len(df) < 3:
        return set()
    mean = df["Review volume"].mean()
    std = df["Review volume"].std()
    if std == 0:
        return set()
    flagged = df[df["Review volume"] > mean + ANOMALY_Z_THRESHOLD * std]
    return set(flagged["week"].tolist())


def render_overview(data: DashboardData) -> None:
    render_html('<div class="rd-section-title">Pipeline overview</div>'
                '<div class="rd-section-sub">Corpus health, theme spread, and weekly review trends '
                'across the ingested Spotify Play Store feed.</div>')

    meta = data.run_metadata
    dates = sorted(r.date for r in data.reviews)
    date_span = f"{dates[0]} → {dates[-1]}" if dates else "—"
    avg_rating = round(sum(r.rating for r in data.reviews) / len(data.reviews), 2) if data.reviews else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Reviews ingested", f"{len(data.reviews):,}")
    c2.metric("Themes discovered", len(data.themes))
    c3.metric("Avg rating", f"{avg_rating}★")
    c4.metric("Analysis sample", meta.get("sample_size", "—"))

    st.caption(f"Date range: {date_span}  ·  Run {meta.get('run_id', '—')}  ·  Model {meta.get('model_id', '—')}")

    st.markdown("####  ")
    left, right = st.columns([1, 1])

    with left:
        render_html('<div class="rd-section-title" style="font-size:1.02rem;">Reviews per theme</div>'
                    '<div class="rd-section-sub">How many sampled reviews support each discovered theme.</div>')
        theme_rows = [
            {"Theme": t.get("label", t.get("theme_id", ""))[:34],
             "Supporting reviews": len(t.get("supporting_review_ids", []))}
            for t in data.themes
        ]
        if theme_rows:
            tdf = pd.DataFrame(theme_rows)
            chart = (
                alt.Chart(tdf)
                .mark_bar(color=SPOTIFY_GREEN, cornerRadiusEnd=4)
                .encode(
                    x=alt.X("Supporting reviews:Q", title="Supporting reviews", axis=_AXIS),
                    y=alt.Y("Theme:N", sort="-x", title=None, axis=_AXIS),
                    tooltip=["Theme", "Supporting reviews"],
                )
                .properties(height=240, background="transparent")
            )
            st.altair_chart(chart, use_container_width=True)

    with right:
        render_html('<div class="rd-section-title" style="font-size:1.02rem;">Weekly review volume</div>'
                    '<div class="rd-section-sub">Number of reviews ingested per ISO week.</div>')
        weekly = _weekly_volume(data.reviews)
        if not weekly.empty:
            vol_chart = (
                alt.Chart(weekly)
                .mark_area(line={"color": SPOTIFY_GREEN}, color=alt.Gradient(
                    gradient="linear",
                    stops=[alt.GradientStop(color="rgba(29,185,84,0.05)", offset=0),
                           alt.GradientStop(color="rgba(29,185,84,0.45)", offset=1)],
                    x1=1, x2=1, y1=1, y2=0))
                .encode(
                    x=alt.X("week:N", title="ISO week", axis=_AXIS),
                    y=alt.Y("Review volume:Q", title="Reviews", axis=_AXIS),
                    tooltip=["week", "Review volume"],
                )
                .properties(height=240, background="transparent")
            )
            st.altair_chart(vol_chart, use_container_width=True)

    weekly = _weekly_volume(data.reviews)
    if not weekly.empty:
        anomalies = _anomaly_weeks(weekly)
        if anomalies:
            render_html(
                '<div class="rd-card" style="border-left:3px solid #F2C744;">'
                '<div class="rd-card-title">⚠ Anomaly weeks flagged</div>'
                f'<div class="rd-card-desc">Unusual review-volume spikes (possible outage or review-bombing): '
                f'<b style="color:#F2C744;">{", ".join(sorted(anomalies))}</b>. '
                'These are flagged rather than blended into evergreen themes.</div></div>'
            )

        render_html('<div class="rd-section-title" style="font-size:1.02rem;margin-top:.6rem;">'
                    'Average rating by week</div>'
                    '<div class="rd-section-sub">Mean star rating per ISO week (1–5).</div>')
        rating_chart = (
            alt.Chart(weekly)
            .mark_line(color=SPOTIFY_GREEN, point=alt.OverlayMarkDef(color=SPOTIFY_GREEN))
            .encode(
                x=alt.X("week:N", title="ISO week", axis=_AXIS),
                y=alt.Y("Average rating:Q", title="Average rating (stars)",
                        scale=alt.Scale(domain=[1, 5]), axis=_AXIS),
                tooltip=["week", "Average rating"],
            )
            .properties(height=220, background="transparent")
        )
        st.altair_chart(rating_chart, use_container_width=True)

    with st.expander("Run metadata (reproducibility)"):
        st.json(meta)
