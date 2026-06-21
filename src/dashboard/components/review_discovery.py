"""Review Discovery tab — searchable, filterable corpus explorer (no PII)."""

from __future__ import annotations

import streamlit as st

from src.dashboard.data_loader import DashboardData
from src.dashboard.style import render_html, review_card

_MAX_RENDER = 40
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
            f'<div style="display:flex;align-items:center;gap:.6rem;margin:.3rem 0;">'
            f'<span style="color:#B3B3B3;font-size:.78rem;width:26px;font-weight:700;">{star}★</span>'
            f'<div style="flex:1;height:8px;background:#282828;border-radius:500px;overflow:hidden;">'
            f'<div style="width:{pct:.1f}%;height:100%;background:{_DIST_COLORS[star]};border-radius:500px;"></div></div>'
            f'<span style="color:#B3B3B3;font-size:.76rem;width:54px;text-align:right;">{counts[star]:,}</span>'
            f'</div>'
        )
    return f'<div class="rd-card"><div class="rd-card-title">Rating distribution</div>{rows}</div>'


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
        render_html(_rating_distribution_html(filtered if filtered else all_reviews))

        render_html(
            '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:.6rem;">'
            '<div class="rd-card-title">Discovered reviews</div>'
            f'<div style="color:#B3B3B3;font-size:.8rem;">'
            f'{min(len(filtered), _MAX_RENDER)} of {len(filtered):,} shown</div></div>'
        )

        if not filtered:
            st.info("No reviews match these filters. Try clearing the search or rating filter.")
            return

        for r in filtered[:_MAX_RENDER]:
            render_html(review_card(
                review_id=r.review_id, rating=r.rating, date=r.date,
                app_version=r.app_version, body=r.body, thumbs_up=r.thumbs_up,
            ))

        if len(filtered) > _MAX_RENDER:
            st.caption(f"Showing first {_MAX_RENDER} of {len(filtered):,}. "
                       "Refine search or rating to narrow results.")
