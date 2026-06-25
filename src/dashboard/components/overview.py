"""Overview tab — pipeline pulse, theme distribution, weekly trend, anomalies."""

from __future__ import annotations

import os
from collections import defaultdict

import altair as alt
import pandas as pd
import streamlit as st

from src.analysis.tags import iso_week
from src.dashboard.constants import ANOMALY_Z_THRESHOLD
from src.dashboard.data_loader import DashboardData
from src.dashboard.exec_summary import generate_executive_summary
from src.dashboard.style import SPOTIFY_GREEN, esc, render_html, week_label

_AXIS = alt.Axis(labelColor="#B3B3B3", titleColor="#FFFFFF", gridColor="#222222",
                 tickColor="#333333", labelLimit=1000, labelFontSize=11)
_WEEK_AXIS = alt.Axis(labelColor="#B3B3B3", titleColor="#FFFFFF", gridColor="#222222",
                      tickColor="#333333", labelAngle=-40, labelFontSize=11)
_WEEK_SORT = alt.SortField(field="week", order="ascending")


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
                "Week": week_label(week),
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


def _render_exec_summary(data: DashboardData) -> None:
    meta = data.run_metadata
    run_id = str(meta.get("run_id", "—"))
    has_key = bool(os.environ.get("GROQ_API_KEY"))

    render_html('<div class="rd-section-title" style="font-size:1.05rem;">AI executive summary</div>'
                '<div class="rd-section-sub">Groq distills the current themes, unmet needs, and rating '
                'mix into a PM-ready brief. Generated once per data refresh and cached (no extra tokens '
                'on re-view).</div>')

    cached = st.session_state.get("exec_summary")
    btn_col, note_col = st.columns([1, 2.4])
    with btn_col:
        label = "Regenerate AI summary" if (cached and cached.get("run_id") == run_id) else "Generate AI summary"
        clicked = st.button(label, use_container_width=True, disabled=not has_key, key="gen_exec_summary")
    with note_col:
        if not has_key:
            st.caption("Add **GROQ_API_KEY** to Secrets to enable the AI executive summary.")
        elif cached and cached.get("run_id") != run_id:
            st.caption("Data was refreshed since the last summary — regenerate for the latest numbers.")

    if clicked:
        with st.spinner("Groq is summarizing the analysis…"):
            try:
                result = generate_executive_summary(data)
                result["run_id"] = run_id
                st.session_state["exec_summary"] = result
                cached = result
            except Exception as exc:  # noqa: BLE001 - surface any Groq/config issue gracefully
                cached = None
                st.session_state.pop("exec_summary", None)
                st.warning(f"Could not generate the summary right now: {exc}")

    if cached and cached.get("run_id") == run_id and cached.get("summary"):
        findings = "".join(
            f'<li style="margin:.35rem 0;color:#D6D6D6;line-height:1.55;">{esc(f)}</li>'
            for f in cached.get("key_findings", [])
        )
        findings_block = (
            f'<div style="color:#fff;font-weight:800;margin:.9rem 0 .2rem 0;">Key findings</div>'
            f'<ul style="margin:0;padding-left:1.1rem;">{findings}</ul>'
            if findings else ""
        )
        render_html(
            '<div class="rd-card accent" style="border-left:3px solid #1DB954;">'
            '<div class="rd-card-title" style="display:flex;align-items:center;gap:.5rem;">'
            '<span>✨ AI-generated summary</span></div>'
            f'<div style="color:#EDEDED;font-size:.96rem;line-height:1.65;margin-top:.4rem;">'
            f'{esc(cached["summary"])}</div>'
            f'{findings_block}'
            '</div>'
        )
        st.caption(f"Groq {cached.get('model', '')} · run {run_id} · cached until next refresh")

    st.markdown("####  ")


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
    _render_exec_summary(data)
    left, right = st.columns([1, 1])

    with left:
        render_html('<div class="rd-section-title" style="font-size:1.02rem;">Reviews per theme</div>'
                    '<div class="rd-section-sub">How many sampled reviews support each discovered theme.</div>')
        theme_rows = [
            {"Theme": t.get("label", t.get("theme_id", "")),
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
                .properties(height=260, background="transparent")
                .configure_view(strokeWidth=0)
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
                    x=alt.X("Week:N", title="Week starting", sort=_WEEK_SORT, axis=_WEEK_AXIS),
                    y=alt.Y("Review volume:Q", title="Reviews", axis=_AXIS),
                    tooltip=["Week", "Review volume"],
                )
                .properties(height=260, background="transparent")
                .configure_view(strokeWidth=0)
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
                x=alt.X("Week:N", title="Week starting", sort=_WEEK_SORT, axis=_WEEK_AXIS),
                y=alt.Y("Average rating:Q", title="Average rating (stars)",
                        scale=alt.Scale(domain=[1, 5]), axis=_AXIS),
                tooltip=["Week", "Average rating"],
            )
            .properties(height=240, background="transparent")
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(rating_chart, use_container_width=True)

    with st.expander("Run metadata (reproducibility)"):
        st.json(meta)
