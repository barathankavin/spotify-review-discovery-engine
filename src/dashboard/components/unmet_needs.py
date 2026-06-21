"""Unmet Needs tab."""

from __future__ import annotations

import streamlit as st

from src.dashboard.data_loader import DashboardData


def _render_quote(text: str) -> None:
    quoted = "\n".join(f"> {line}" if line else ">" for line in text.splitlines())
    st.markdown(quoted)


def render_unmet_needs(data: DashboardData) -> None:
    st.subheader("Unmet Needs")
    st.caption("Ranked by signal strength (1 = highest). Discovery & recommendations scope.")

    if not data.unmet_needs:
        st.info("No unmet needs in artifacts.")
        return

    for need in data.unmet_needs:
        rank = need.get("rank", "—")
        statement = need.get("statement", "")
        rids = need.get("supporting_review_ids", [])

        st.markdown(f"### #{rank}")
        st.write(statement)

        for rid in rids:
            review = data.reviews_by_id.get(rid)
            if review:
                _render_quote(review.body[:300] if len(review.body) > 300 else review.body)
                st.caption(
                    f"review_id: `{rid}`  ·  {review.date}  ·  {review.rating}★"
                )
            else:
                st.caption(f"review_id: `{rid}` (not in corpus)")

        st.divider()
