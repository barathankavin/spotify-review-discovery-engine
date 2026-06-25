"""Review Discovery tab — searchable, filterable corpus explorer (no PII)."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.dashboard.data_loader import DashboardData
from src.dashboard.style import render_html, review_card

_PAGE_SIZE = 20
_DIST_COLORS = {5: "#1DB954", 4: "#1DB954", 3: "#F2C744", 2: "#FF8A5B", 1: "#E22134"}


def _rating_distribution_html(reviews) -> str:
    counts = {s: 0 for s in range(1, 6)}
    for r in reviews:
        if r.rating in counts:
            counts[r.rating] += 1
    total = sum(counts.values()) or 1
    rows = ""
    for star in range(5, 0, -1):
        pct = 100 * counts[star] / total
        rows += (
            f'<div style="display:flex;align-items:center;gap:.8rem;margin:.55rem 0;">'
            f'<span style="color:#FFFFFF;font-size:.95rem;width:34px;font-weight:800;">{star}★</span>'
            f'<div style="flex:1;height:18px;background:#282828;border-radius:500px;overflow:hidden;">'
            f'<div style="width:{pct:.1f}%;height:100%;background:{_DIST_COLORS[star]};border-radius:500px;"></div></div>'
            f'<span style="color:#B3B3B3;font-size:.9rem;width:96px;text-align:right;">'
            f'{counts[star]:,} · {pct:.0f}%</span>'
            f'</div>'
        )
    return (
        '<div class="rd-card"><div class="rd-card-title" style="font-size:1.02rem;">'
        'Rating distribution</div>'
        f'<div style="margin-top:.5rem;">{rows}</div></div>'
    )


def _sentiment_breakdown_chart(reviews):
    """Rating-based sentiment proxy (we store ratings, not LLM sentiment labels)."""
    pos = sum(1 for r in reviews if r.rating >= 4)
    neu = sum(1 for r in reviews if r.rating == 3)
    neg = sum(1 for r in reviews if r.rating <= 2)
    df = pd.DataFrame(
        [
            {"Sentiment": "Positive (4–5★)", "Reviews": pos},
            {"Sentiment": "Neutral (3★)", "Reviews": neu},
            {"Sentiment": "Negative (1–2★)", "Reviews": neg},
        ]
    )
    domain = ["Positive (4–5★)", "Neutral (3★)", "Negative (1–2★)"]
    rng = ["#1DB954", "#9E9E9E", "#E22134"]
    return (
        alt.Chart(df)
        .mark_arc(innerRadius=62, cornerRadius=3, stroke="#121212", strokeWidth=2)
        .encode(
            theta=alt.Theta("Reviews:Q", stack=True),
            color=alt.Color(
                "Sentiment:N",
                scale=alt.Scale(domain=domain, range=rng),
                legend=alt.Legend(
                    title=None, labelColor="#E6E6E6", labelFontSize=12, orient="bottom"
                ),
            ),
            tooltip=["Sentiment", "Reviews"],
        )
        .properties(height=280, background="transparent")
        .configure_view(strokeWidth=0)
    )


def render_review_discovery(data: DashboardData) -> None:
    render_html('<div class="rd-section-title">Review discovery</div>'
                '<div class="rd-section-sub">Explore the full normalized corpus. Cards show rating, date, '
                'app version, and helpful votes — never reviewer identity.</div>')

    all_reviews = data.reviews

    # Sidebar-style filter column + results column
    fcol, rcol = st.columns([1, 2.6], gap="large")

    with fcol:
        render_html('<div class="rd-card-title">Filters</div>')
        query = st.text_input("Search reviews", placeholder="Keywords, e.g. shuffle, ads, playlist")
        rating_choice = st.radio(
            "Rating", ["All", "5★", "4★", "3★", "2★", "1★"], horizontal=True, key="rd_rating"
        )
        sort_choice = st.selectbox(
            "Sort by", ["Newest first", "Oldest first", "Most helpful", "Lowest rating", "Highest rating"]
        )
        if st.button("Reset filters", use_container_width=True):
            for k in ("rd_rating",):
                st.session_state.pop(k, None)
            st.rerun()

    # Apply filters
    filtered = all_reviews
    if query.strip():
        q = query.strip().lower()
        filtered = [r for r in filtered if q in r.body.lower()]
    if rating_choice != "All":
        target = int(rating_choice[0])
        filtered = [r for r in filtered if r.rating == target]

    if sort_choice == "Newest first":
        filtered = sorted(filtered, key=lambda r: r.date, reverse=True)
    elif sort_choice == "Oldest first":
        filtered = sorted(filtered, key=lambda r: r.date)
    elif sort_choice == "Most helpful":
        filtered = sorted(filtered, key=lambda r: r.thumbs_up, reverse=True)
    elif sort_choice == "Lowest rating":
        filtered = sorted(filtered, key=lambda r: r.rating)
    else:
        filtered = sorted(filtered, key=lambda r: r.rating, reverse=True)

    avg = round(sum(r.rating for r in filtered) / len(filtered), 2) if filtered else 0.0

    with rcol:
        m1, m2, m3 = st.columns(3)
        m1.metric("Avg rating", f"{avg}★")
        m2.metric("Matching reviews", f"{len(filtered):,}")
        m3.metric("Corpus total", f"{len(all_reviews):,}")

        dist_col, sent_col = st.columns([1.15, 1], gap="large")
        chart_source = filtered if filtered else all_reviews
        with dist_col:
            render_html(_rating_distribution_html(chart_source))
        with sent_col:
            render_html('<div class="rd-card-title" style="font-size:1.02rem;">'
                        'Sentiment breakdown</div>'
                        '<div class="rd-section-sub" style="margin-top:.1rem;">'
                        'Rating-based proxy (4–5★ positive · 3★ neutral · 1–2★ negative).</div>')
            st.altair_chart(_sentiment_breakdown_chart(chart_source), use_container_width=True)

        if not filtered:
            st.info("No reviews match these filters. Try clearing the search or rating filter.")
            return

        # Reset to page 1 whenever the active filter/sort changes.
        sig = (query.strip().lower(), rating_choice, sort_choice)
        if st.session_state.get("rd_filter_sig") != sig:
            st.session_state["rd_filter_sig"] = sig
            st.session_state["rd_page"] = 0

        total_pages = max(1, (len(filtered) + _PAGE_SIZE - 1) // _PAGE_SIZE)
        page = min(st.session_state.get("rd_page", 0), total_pages - 1)
        start = page * _PAGE_SIZE
        end = min(start + _PAGE_SIZE, len(filtered))

        render_html(
            '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:.6rem;">'
            '<div class="rd-card-title">Discovered reviews</div>'
            f'<div style="color:#B3B3B3;font-size:.8rem;">'
            f'{start + 1:,}–{end:,} of {len(filtered):,}</div></div>'
        )

        for r in filtered[start:end]:
            render_html(review_card(
                review_id=r.review_id, rating=r.rating, date=r.date,
                app_version=r.app_version, body=r.body, thumbs_up=r.thumbs_up,
            ))

        prev_col, info_col, next_col = st.columns([1, 1.6, 1])
        with prev_col:
            if st.button("← Previous", use_container_width=True,
                         disabled=page <= 0, key="rd_prev"):
                st.session_state["rd_page"] = page - 1
                st.rerun()
        with info_col:
            render_html(
                f'<div style="text-align:center;color:#B3B3B3;font-size:.85rem;padding-top:.45rem;">'
                f'Page <b style="color:#fff;">{page + 1}</b> of {total_pages}</div>'
            )
        with next_col:
            if st.button("Next →", use_container_width=True,
                         disabled=page >= total_pages - 1, key="rd_next"):
                st.session_state["rd_page"] = page + 1
                st.rerun()
