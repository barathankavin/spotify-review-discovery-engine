"""Top product header: brand, live pipeline status, sync time, refresh action."""

from __future__ import annotations

import streamlit as st

from src.dashboard.pipeline_status import PipelineStatus
from src.dashboard.style import render_html

_HEADER_CSS = """
<style>
.rd-header { display:flex; align-items:center; gap:1rem; margin:.2rem 0 1.4rem 0; flex-wrap:wrap; }
.rd-logo { width:52px; height:52px; border-radius:14px; background:linear-gradient(135deg,#1DB954,#11833b);
    display:flex; align-items:center; justify-content:center; flex-shrink:0; box-shadow:0 6px 20px rgba(29,185,84,.25); }
.rd-logo span { display:block; width:5px; border-radius:4px; background:#0A0A0A; margin:0 1.5px; }
.rd-logo .b1 { height:14px; } .rd-logo .b2 { height:24px; } .rd-logo .b3 { height:18px; }
.rd-brand-eyebrow { color:#1DB954; font-size:.7rem; font-weight:800; letter-spacing:.18em; text-transform:uppercase; margin:0; }
.rd-brand-title { color:#fff; font-size:1.9rem; font-weight:900; letter-spacing:-.03em; margin:.05rem 0 .1rem 0; line-height:1; }
.rd-brand-sub { color:#B3B3B3; font-size:.82rem; margin:0; }
.rd-brand-sub b { color:#fff; font-weight:700; }
.rd-status-pill { display:inline-flex; align-items:center; gap:.45rem; background:rgba(29,185,84,.14);
    color:#1ED760; font-size:.72rem; font-weight:700; padding:.35rem .8rem; border-radius:500px; }
.rd-status-pill.off { background:rgba(226,33,52,.16); color:#FF6B6B; }
.rd-dot { width:8px; height:8px; border-radius:50%; background:#1ED760; box-shadow:0 0 0 0 rgba(30,215,96,.6); animation:rdpulse 1.8s infinite; }
.rd-status-pill.off .rd-dot { background:#FF6B6B; animation:none; }
@keyframes rdpulse { 0%{box-shadow:0 0 0 0 rgba(30,215,96,.5);} 70%{box-shadow:0 0 0 7px rgba(30,215,96,0);} 100%{box-shadow:0 0 0 0 rgba(30,215,96,0);} }
.rd-synced { color:#B3B3B3; font-size:.75rem; text-align:right; line-height:1.4; }
.rd-synced b { color:#fff; }
</style>
"""

_LOGO = (
    '<div class="rd-logo"><span class="b1"></span><span class="b2"></span>'
    '<span class="b3"></span></div>'
)


def render_header(status: PipelineStatus) -> None:
    render_html(_HEADER_CSS)

    pill_class = "rd-status-pill" if status.online else "rd-status-pill off"
    pill_text = "Pipeline online" if status.online else "Pipeline offline"
    engine = "Groq LLM" if status.is_llm else "Keyword baseline"

    left, right = st.columns([4, 1])
    with left:
        render_html(
            f"""
            <div class="rd-header">
              {_LOGO}
              <div>
                <p class="rd-brand-eyebrow">NL · AI Review Engine</p>
                <h1 class="rd-brand-title">Review Discovery Engine</h1>
                <p class="rd-brand-sub">Live feed from <b>Spotify Play Store</b> · Google Play ·
                    {status.review_count:,} reviews · {engine}</p>
              </div>
            </div>
            """
        )
    with right:
        render_html(
            f"""
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:.5rem;padding-top:.3rem;">
              <span class="{pill_class}"><span class="rd-dot"></span>{pill_text}</span>
              <div class="rd-synced">Synced <b>{status.synced_label}</b><br>{status.synced_local}</div>
            </div>
            """
        )
        if st.button("Refresh pipeline", key="refresh_pipeline", use_container_width=True):
            st.cache_data.clear()
            st.session_state["_pipeline_refreshed"] = True
            st.rerun()

    if st.session_state.pop("_pipeline_refreshed", False):
        st.toast("Reloaded latest artifacts from disk.", icon="✅")
