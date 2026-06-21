"""Spotify-inspired design system: global CSS + reusable HTML card helpers.

All review cards are grounded in non-PII fields only (review_id, rating, date,
app_version, thumbs_up) per problemStatement.md sections 5.2 and 11.
"""

from __future__ import annotations

import html
from datetime import date

import streamlit as st

SPOTIFY_GREEN = "#1DB954"
SPOTIFY_GREEN_BRIGHT = "#1ED760"
BG = "#0A0A0A"
CARD_BG = "#181818"
CARD_BG_HOVER = "#1F1F1F"
BORDER = "#282828"
TEXT = "#FFFFFF"
TEXT_MUTED = "#B3B3B3"

_GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"], .stApp, button, input, textarea, select {
    font-family: 'Montserrat', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
}

.stApp { background-color: #0A0A0A; }

/* Hide default Streamlit chrome for a cleaner product look */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 3rem !important; max-width: 1200px; }

/* Entry animation */
@keyframes fadeUp { 0% { opacity: 0; transform: translateY(16px); } 100% { opacity: 1; transform: translateY(0); } }
@keyframes pop { 0% { opacity: 0; transform: scale(.97); } 100% { opacity: 1; transform: scale(1); } }
.block-container > div { animation: fadeUp .5s cubic-bezier(.2,.8,.2,1); }

h1, h2, h3, h4, h5, h6 { color: #FFFFFF !important; font-weight: 800 !important; letter-spacing: -.02em !important; }

/* Tabs -> Spotify nav pills */
.stTabs [data-baseweb="tab-list"] { gap: .5rem; border-bottom: none; background: transparent; }
.stTabs [data-baseweb="tab"] {
    background: #181818 !important; border-radius: 500px !important; padding: .45rem 1.25rem !important;
    color: #B3B3B3 !important; font-weight: 700 !important; font-size: .85rem !important; border: none !important;
    transition: all .25s ease !important;
}
.stTabs [data-baseweb="tab"]:hover { color: #FFFFFF !important; background: #282828 !important; }
.stTabs [aria-selected="true"] { background: #1DB954 !important; color: #000000 !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none !important; }

/* Buttons -> green pills */
.stButton > button {
    border-radius: 500px !important; font-weight: 700 !important; letter-spacing: .04em !important;
    border: none !important; background: #1DB954 !important; color: #000 !important;
    padding: .5rem 1.5rem !important; transition: all .2s ease !important;
}
.stButton > button:hover { transform: scale(1.04); background: #1ED760 !important; color: #000 !important; }
.stButton > button:focus { box-shadow: none !important; color: #000 !important; }

/* Inputs */
input, textarea, div[data-baseweb="input"] input, [data-testid="stChatInput"] textarea {
    background: #282828 !important; color: #FFFFFF !important; border-radius: 8px !important; border: 1px solid transparent !important;
}
div[data-baseweb="select"] > div, div[data-baseweb="input"] {
    background: #282828 !important; border-radius: 8px !important; border: 1px solid transparent !important; color: #fff !important;
}
div[data-baseweb="select"]:hover > div { border-color: #1DB954 !important; }
label, .stRadio label, .stSelectbox label { color: #B3B3B3 !important; font-weight: 600 !important; }

/* Radio chips */
.stRadio [role="radiogroup"] { gap: .4rem; flex-wrap: wrap; }

/* Metrics */
[data-testid="stMetric"] {
    background: #181818; border: 1px solid #282828; border-radius: 12px; padding: 1.1rem 1.25rem;
    transition: border-color .25s ease, transform .25s ease;
}
[data-testid="stMetric"]:hover { border-color: #1DB954; transform: translateY(-2px); }
[data-testid="stMetricValue"] { font-weight: 800 !important; font-size: 2.2rem !important; color: #FFFFFF !important; }
[data-testid="stMetricLabel"] { color: #B3B3B3 !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: .06em; font-size: .72rem !important; }

/* Chat */
.stChatMessage { background: #181818 !important; border: 1px solid #282828 !important; border-radius: 14px !important; animation: pop .35s ease; }

/* Expander */
[data-testid="stExpander"] { border: 1px solid #282828 !important; border-radius: 12px !important; background: #141414 !important; }
.streamlit-expanderHeader, [data-testid="stExpander"] summary { color: #FFFFFF !important; font-weight: 600 !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid #282828 !important; border-radius: 12px !important; overflow: hidden; }

/* Blockquote */
blockquote { border-left: 4px solid #1DB954 !important; padding: .25rem 0 .25rem 1rem !important; color: #B3B3B3 !important; font-style: italic; margin: .75rem 0 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: #282828; border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: #3a3a3a; }

/* ---- custom card primitives ---- */
.rd-card {
    background: #181818; border: 1px solid #282828; border-radius: 14px; padding: 1.1rem 1.25rem;
    margin-bottom: .85rem; transition: background .25s ease, border-color .25s ease, transform .25s ease;
    animation: fadeUp .45s cubic-bezier(.2,.8,.2,1);
}
.rd-card:hover { background: #1F1F1F; border-color: #3a3a3a; transform: translateY(-2px); }
.rd-card.accent { border-left: 3px solid #1DB954; }

.rd-card-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: .5rem; }
.rd-card-title { color: #FFFFFF; font-weight: 700; font-size: 1.02rem; line-height: 1.35; margin: 0; }
.rd-card-desc { color: #B3B3B3; font-size: .9rem; line-height: 1.5; margin: .25rem 0 .6rem 0; }

.rd-badge { display: inline-flex; align-items: center; gap: .35rem; background: rgba(29,185,84,.14); color: #1ED760;
    font-size: .68rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; padding: .25rem .6rem; border-radius: 500px; white-space: nowrap; }
.rd-badge.warn { background: rgba(244,180,0,.14); color: #F2C744; }
.rd-badge.neg { background: rgba(226,33,52,.16); color: #FF6B6B; }
.rd-badge.muted { background: #282828; color: #B3B3B3; }

.rd-meta { display: flex; flex-wrap: wrap; gap: .9rem; color: #6f6f6f; font-size: .76rem; font-weight: 600; letter-spacing: .02em; }
.rd-meta b { color: #B3B3B3; font-weight: 700; }
.rd-stars { color: #1DB954; letter-spacing: 1px; }
.rd-stars .off { color: #404040; }

.rd-section-title { color: #FFFFFF; font-weight: 800; font-size: 1.15rem; letter-spacing: -.02em; margin: .2rem 0 .15rem 0; }
.rd-section-sub { color: #B3B3B3; font-size: .85rem; margin: 0 0 .9rem 0; }

.rd-quote { border-left: 3px solid #1DB954; padding: .1rem 0 .1rem .9rem; color: #C9C9C9; font-style: italic; font-size: .9rem; margin: .5rem 0; }

.rd-pill-row { display: flex; flex-wrap: wrap; gap: .4rem; margin: .2rem 0 .6rem 0; }
</style>
"""


def inject_global_css() -> None:
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


def esc(text: str) -> str:
    return html.escape(str(text or ""))


def week_label(iso_week_str: str) -> str:
    """Convert '2026-W15' to a readable 'Apr 06' (week-start date)."""
    try:
        year, week = iso_week_str.split("-W")
        return date.fromisocalendar(int(year), int(week), 1).strftime("%b %d")
    except (ValueError, AttributeError):
        return iso_week_str


def stars(rating: int) -> str:
    rating = max(0, min(5, int(rating or 0)))
    on = "★" * rating
    off = f'<span class="off">{"★" * (5 - rating)}</span>'
    return f'<span class="rd-stars">{on}{off}</span>'


def rating_badge_class(rating: int) -> str:
    if rating <= 2:
        return "neg"
    if rating == 3:
        return "warn"
    return ""


def review_card(*, review_id: str, rating: int, date: str, app_version: str,
                body: str, thumbs_up: int = 0, similarity: float | None = None,
                max_chars: int = 360) -> str:
    text = esc(body)
    if len(body or "") > max_chars:
        text = esc(body[:max_chars].rsplit(" ", 1)[0]) + "…"

    meta_bits = [f"<span><b>{esc(date)}</b></span>"]
    if app_version:
        meta_bits.append(f"<span>v{esc(app_version)}</span>")
    if thumbs_up:
        meta_bits.append(f"<span>👍 {int(thumbs_up)}</span>")
    if similarity is not None:
        meta_bits.append(f"<span>match {similarity:.0%}</span>")
    meta_bits.append(f"<span>id <b>{esc(review_id[:8])}</b></span>")

    return f"""
    <div class="rd-card">
      <div class="rd-card-head">
        <div class="rd-meta">{stars(rating)}</div>
      </div>
      <div class="rd-card-desc" style="color:#E0E0E0;">{text}</div>
      <div class="rd-meta">{''.join(meta_bits)}</div>
    </div>
    """


def render_html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)
