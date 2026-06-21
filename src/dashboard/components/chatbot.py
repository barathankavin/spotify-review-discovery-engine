"""Discovery chat panel — grounded RAG Q&A (column-friendly, no st.chat_input)."""

from __future__ import annotations

import os

import streamlit as st

from src.ops.ensure_vector_store import ensure_vector_store
from src.dashboard.style import esc, render_html, stars
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
    engine = os.getenv("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")
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
        render_html(f'<div class="rd-card accent"><div style="color:#E8E8E8;font-size:.92rem;'
                    f'line-height:1.6;white-space:pre-wrap;">{esc(result.answer)}</div></div>')
        if result.meta.get("fallback"):
            st.caption(f"Retrieval-only fallback · {result.meta.get('fallback_reason', 'n/a')}")
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
