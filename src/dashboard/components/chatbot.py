"""Discovery chat panel — grounded RAG Q&A (column-friendly, no st.chat_input)."""

from __future__ import annotations

import os

import streamlit as st

from src.ops.ensure_vector_store import ensure_vector_store
from src.dashboard.bootstrap import secret_key_names
from src.dashboard.style import esc, format_chat_answer, render_html, stars
from src.rag.pipeline import ChatResult, answer_question
from src.rag.retriever import ReviewRetriever

SUGGESTED = [
    "Why do users struggle to discover new music?",
    "What are the most common frustrations with recommendations?",
    "What listening behaviors are users trying to achieve?",
    "What causes users to repeatedly listen to the same content?",
    "Which user segments experience different discovery challenges?",
    "What unmet needs emerge consistently across reviews?",
]


@st.cache_resource(show_spinner="Loading embedding model…")
def _get_retriever() -> ReviewRetriever:
    return ReviewRetriever()


def _ensure_store_once() -> dict:
    if st.session_state.get("vector_store_ready"):
        return st.session_state.get("vector_store_status", {})
    with st.spinner("Checking search index…"):
        status = ensure_vector_store()
    st.session_state.vector_store_ready = True
    st.session_state.vector_store_status = status
    return status


def _render_sources(result: ChatResult) -> None:
    if not result.retrieved:
        return
    with st.expander(f"Source reviews ({len(result.retrieved)} retrieved · cited by review_id)"):
        for item in result.retrieved:
            doc = esc(item.document[:380]) + ("…" if len(item.document) > 380 else "")
            render_html(
                f'<div class="rd-card" style="margin-bottom:.5rem;padding:.8rem 1rem;">'
                f'<div class="rd-meta" style="margin-bottom:.4rem;">{stars(item.rating)}'
                f'<span><b>{esc(item.date)}</b></span>'
                f'<span>match {item.similarity:.0%}</span>'
                f'<span>id <b>{esc(item.review_id[:8])}</b></span></div>'
                f'<div style="color:#C9C9C9;font-size:.86rem;line-height:1.5;">{doc}</div></div>'
            )


def _render_key_diagnostic() -> None:
    secret_names = secret_key_names(st)
    env_has_key = bool(os.environ.get("GROQ_API_KEY"))
    with st.expander("Why isn't Groq running? (config diagnostic)"):
        st.markdown(
            "The app cannot read **`GROQ_API_KEY`**. Fix it in "
            "**Manage app → Settings → Secrets** (Streamlit Cloud) and **reboot**."
        )
        if secret_names:
            st.markdown(
                "Secret key names the app currently sees (values hidden): "
                + ", ".join(f"`{n}`" for n in secret_names)
            )
            if "GROQ_API_KEY" not in secret_names:
                st.warning(
                    "`GROQ_API_KEY` is **not** among the visible secret names — "
                    "check for a typo or a wrong key name."
                )
        else:
            st.warning(
                "No secrets are visible at all. Paste this into the Secrets box "
                "(top level, no section header) and save:"
            )
        st.code('GROQ_API_KEY = "gsk_your_real_key_here"', language="toml")
        st.caption(f"GROQ_API_KEY present in environment: {env_has_key}")


def _answer_and_store(prompt: str, retriever: ReviewRetriever) -> None:
    with st.spinner("Groq is analyzing matched reviews…"):
        result = answer_question(prompt, retriever)
    st.session_state.chat_history.append((prompt, result))


def render_chat_panel() -> None:
    render_html(
        '<div class="rd-section-title">Discovery chat</div>'
        '<div class="rd-section-sub">Grounded in retrieved review excerpts only. Every claim cites a '
        'review_id; out-of-scope questions are refused.</div>'
    )

    _ensure_store_once()
    retriever = _get_retriever()
    engine = os.getenv("GROQ_CHAT_MODEL", "llama-3.1-8b-instant")
    render_html(f'<div class="rd-pill-row"><span class="rd-badge muted">Groq · {esc(engine)}</span>'
                f'<span class="rd-badge muted">{retriever.corpus_size:,} reviews indexed</span></div>')

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.caption("Try a starter question:")
    cols = st.columns(2)
    for i, q in enumerate(SUGGESTED):
        if cols[i % 2].button(q, key=f"sugg_{i}", use_container_width=True):
            _answer_and_store(q, retriever)
            st.rerun()

    with st.form("chat_form", clear_on_submit=True):
        prompt = st.text_input("Ask discovery & recommendation questions",
                               placeholder="e.g. Why do users feel stuck in a loop?",
                               label_visibility="collapsed")
        submitted = st.form_submit_button("Ask Groq", use_container_width=True)
    if submitted and prompt.strip():
        _answer_and_store(prompt, retriever)
        st.rerun()

    for question, result in reversed(st.session_state.chat_history[-5:]):
        render_html(f'<div class="rd-card" style="border-left:3px solid #404040;">'
                    f'<div class="rd-meta" style="margin-bottom:.35rem;"><span>YOU ASKED</span></div>'
                    f'<div style="color:#fff;font-weight:600;">{esc(question)}</div></div>')
        render_html(f'<div class="rd-card accent">{format_chat_answer(result.answer)}</div>')
        if result.meta.get("fallback"):
            reason = result.meta.get("fallback_reason", "n/a")
            st.caption(f"Retrieval-only fallback · {reason}")
            if "GROQ_API_KEY" in str(reason):
                _render_key_diagnostic()
        elif result.groq_called:
            st.caption(f"Groq {result.meta.get('model', '')} · top match {result.max_similarity:.0%}")
        elif result.refused:
            st.caption(f"Refused · top match {result.max_similarity:.0%} "
                       f"(threshold {os.getenv('RAG_SIMILARITY_THRESHOLD', '0.30')})")
        _render_sources(result)

    if st.session_state.chat_history and st.button("Clear chat", key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()


# Backward-compatible name used elsewhere
def render_chatbot() -> None:
    render_chat_panel()
