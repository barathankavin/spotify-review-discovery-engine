"""Top product header: brand, live pipeline status, sync time, refresh action."""

from __future__ import annotations

import streamlit as st

from src.dashboard.pipeline_status import PipelineStatus
from src.dashboard.style import render_html

_HEADER_CSS = """
<style>
.rd-header { display:flex; align-items:center; gap:1rem; margin:.2rem 0 1.4rem 0; flex-wrap:wrap; }
.rd-logo { width:54px; height:54px; flex-shrink:0; filter:drop-shadow(0 6px 18px rgba(29,185,84,.3)); }
.rd-logo svg { width:54px; height:54px; display:block; }
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
.rd-mobile-badge { display:inline-flex; align-items:center; gap:.35rem; background:#282828; color:#B3B3B3;
    font-size:.68rem; font-weight:700; padding:.25rem .6rem; border-radius:500px; }
@media (max-width:640px) {
    .rd-synced { text-align:left; }
    .rd-brand-title { font-size:1.45rem; }
}
</style>
"""

_LOGO = (
    '<div class="rd-logo"><svg viewBox="0 0 168 168" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spotify">'
    '<circle cx="84" cy="84" r="84" fill="#1DB954"/>'
    '<g fill="none" stroke="#0A0A0A" stroke-linecap="round">'
    '<path stroke-width="15" d="M40 62 C 80 50, 120 56, 134 68"/>'
    '<path stroke-width="13" d="M46 88 C 82 78, 116 83, 130 93"/>'
    '<path stroke-width="11" d="M52 111 C 82 103, 110 107, 122 115"/>'
    '</g></svg></div>'
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
                <div style="margin-top:.4rem;">
                    <span class="rd-mobile-badge">📱 Mobile-friendly · works on phone &amp; desktop</span>
                </div>
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
