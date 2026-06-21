"""Theme discovery cards + per-theme deep-dive (grounded in review_ids only)."""

from __future__ import annotations

from collections import Counter

import altair as alt
import pandas as pd
import streamlit as st

from src.analysis.tags import iso_week
from src.dashboard.constants import MAX_SUMMARY_WORDS
from src.dashboard.data_loader import DashboardData
from src.dashboard.style import SPOTIFY_GREEN, esc, render_html, review_card, stars, week_label

_AXIS = alt.Axis(labelColor="#B3B3B3", titleColor="#FFFFFF", gridColor="#222222",
                 tickColor="#333333", labelLimit=1000, labelFontSize=11)
_WEEK_AXIS = alt.Axis(labelColor="#B3B3B3", titleColor="#FFFFFF", gridColor="#222222",
                      tickColor="#333333", labelAngle=-40, labelFontSize=11)


def _theme_stats(theme: dict, data: DashboardData, total: int) -> dict:
    rids = theme.get("supporting_review_ids", [])
    ratings = [data.reviews_by_id[r].rating for r in rids if r in data.reviews_by_id]
    avg = round(sum(ratings) / len(ratings), 1) if ratings else 0.0
    count = len(rids)
    pct = round(100 * count / total, 1) if total else 0.0
    severity = round(count * (5 - avg), 1)
    return {"count": count, "avg": avg, "pct": pct, "severity": severity}


def _trend_badge(avg: float) -> str:
    if avg <= 2.2:
        return '<span class="rd-badge neg">▲ High friction</span>'
    if avg <= 3.2:
        return '<span class="rd-badge warn">▲ Trending up</span>'
    return '<span class="rd-badge">● Stable</span>'


def render_theme_cards(data: DashboardData) -> None:
    total = len(data.reviews) or 1
    render_html(
        '<div style="display:flex;justify-content:space-between;align-items:baseline;">'
        '<div class="rd-section-title">Theme discovery</div>'
        f'<div style="color:#B3B3B3;font-size:.8rem;font-weight:600;">{len(data.themes)} active themes</div>'
        '</div>'
        '<div class="rd-section-sub">Discovery & recommendation pain clusters mined from review text. '
        'Cited by internal review_id only — no reviewer identity.</div>'
    )

    if not data.themes:
        st.warning("No themes in artifacts.")
        return

    for idx, theme in enumerate(data.themes):
        s = _theme_stats(theme, data, total)
        label = esc(theme.get("label", theme.get("theme_id", "")))
        render_html(
            f"""
            <div class="rd-card accent" style="margin-bottom:.35rem;">
              <div class="rd-card-head">
                <div class="rd-card-title">{label}</div>
                {_trend_badge(s['avg'])}
              </div>
              <div class="rd-card-desc">Cluster of {s['count']} sampled reviews · average rating {s['avg']}★</div>
              <div class="rd-meta">
                <span><b>{s['count']}</b> reviews</span>
                <span><b>{s['pct']}%</b> of corpus</span>
                <span>severity <b>{s['severity']}</b></span>
              </div>
            </div>
            """
        )
        with st.expander(f"View supporting reviews ({s['count']})"):
            rids = theme.get("supporting_review_ids", [])
            shown = 0
            for rid in rids:
                review = data.reviews_by_id.get(rid)
                if not review:
                    continue
                render_html(review_card(
                    review_id=review.review_id, rating=review.rating, date=review.date,
                    app_version=review.app_version, body=review.body, thumbs_up=review.thumbs_up,
                ))
                shown += 1
                if shown >= 12:
                    break
            if shown == 0:
                st.info("Supporting reviews are outside the current corpus snapshot.")
            elif len(rids) > shown:
                st.caption(f"Showing {shown} of {len(rids)} supporting reviews.")


def _weekly_counts(theme: dict, data: DashboardData) -> pd.DataFrame:
    counts: Counter[str] = Counter()
    for rid in theme.get("supporting_review_ids", []):
        review = data.reviews_by_id.get(rid)
        if review:
            counts[iso_week(review.date)] += 1
    if not counts:
        return pd.DataFrame(columns=["week", "Week", "count"])
    return pd.DataFrame(
        [{"week": w, "Week": week_label(w), "count": counts[w]} for w in sorted(counts)]
    )


def render_theme_deepdive(data: DashboardData) -> None:
    if not data.themes:
        return
    render_html('<div class="rd-section-title" style="margin-top:1.2rem;">Theme deep-dive</div>')

    labels = [t.get("label", t.get("theme_id", "")) for t in data.themes]
    selected = st.selectbox("Select a theme to explore", labels, key="theme_select")
    theme = next(t for t in data.themes if t.get("label") == selected)

    summary = theme.get("summary", "") or theme.get("description", "")
    words = summary.split()
    truncated = len(words) > MAX_SUMMARY_WORDS
    display = " ".join(words[:MAX_SUMMARY_WORDS]) + (" …" if truncated else "")

    left, right = st.columns([1.4, 1])
    with left:
        render_html(f'<div class="rd-card"><div class="rd-card-title">Summary</div>'
                    f'<div class="rd-card-desc">{esc(display)}</div>'
                    f'<div class="rd-meta"><span>{len(display.split())} words '
                    f'(≤{MAX_SUMMARY_WORDS})</span>'
                    f'<span><b>{len(theme.get("supporting_review_ids", []))}</b> supporting reviews</span></div></div>')

        quotes = theme.get("quotes", [])
        if quotes:
            render_html('<div class="rd-card-title" style="margin-top:.4rem;">Verbatim quotes</div>')
            for q in quotes:
                rid = esc(q.get("review_id", ""))
                txt = esc(q.get("text", ""))
                render_html(f'<div class="rd-quote">“{txt}”<div class="rd-meta" '
                            f'style="margin-top:.3rem;"><span>review_id <b>{rid[:8]}</b></span></div></div>')

    with right:
        render_html('<div class="rd-card-title">Frequency by week</div>')
        wdf = _weekly_counts(theme, data)
        if wdf.empty:
            st.info("No dated reviews for this theme.")
        else:
            chart = (
                alt.Chart(wdf)
                .mark_bar(color=SPOTIFY_GREEN, cornerRadiusEnd=3)
                .encode(
                    x=alt.X("Week:N", title="Week starting",
                            sort=alt.SortField(field="week", order="ascending"), axis=_WEEK_AXIS),
                    y=alt.Y("count:Q", title="Reviews in theme", axis=_AXIS),
                    tooltip=["Week", "count"],
                )
                .properties(height=260, background="transparent")
                .configure_view(strokeWidth=0)
            )
            st.altair_chart(chart, use_container_width=True)


def render_themes(data: DashboardData) -> None:
    """Backward-compatible full themes view."""
    render_theme_cards(data)
    render_theme_deepdive(data)
