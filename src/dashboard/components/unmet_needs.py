"""Unmet Needs tab — ranked 'I wish / I want / why can't' statements."""

from __future__ import annotations

import streamlit as st

from src.dashboard.data_loader import DashboardData
from src.dashboard.style import esc, render_html, stars


def render_unmet_needs(data: DashboardData) -> None:
    render_html('<div class="rd-section-title">Unmet needs</div>'
                '<div class="rd-section-sub">Recurring desires distilled from review language, ranked by '
                'signal strength (1 = strongest). Discovery & recommendation scope.</div>')

    if not data.unmet_needs:
        st.info("No unmet needs in artifacts.")
        return

    for need in data.unmet_needs:
        rank = need.get("rank", "—")
        statement = esc(need.get("statement", ""))
        rids = need.get("supporting_review_ids", [])

        quotes_html = ""
        for rid in rids:
            review = data.reviews_by_id.get(rid)
            if review:
                body = esc(review.body[:260]) + ("…" if len(review.body) > 260 else "")
                quotes_html += (
                    f'<div class="rd-quote">“{body}”<div class="rd-meta" style="margin-top:.3rem;">'
                    f'{stars(review.rating)}<span><b>{esc(review.date)}</b></span>'
                    f'<span>id <b>{esc(rid[:8])}</b></span></div></div>'
                )
            else:
                quotes_html += f'<div class="rd-meta"><span>review_id <b>{esc(rid[:8])}</b> (not in corpus)</span></div>'

        render_html(
            f"""
            <div class="rd-card accent">
              <div class="rd-card-head">
                <div class="rd-card-title">{statement}</div>
                <span class="rd-badge">#{rank}</span>
              </div>
              {quotes_html}
            </div>
            """
        )
