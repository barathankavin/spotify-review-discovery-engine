"""Chatbot tab — grounded RAG Q&A over review corpus."""

from __future__ import annotations

import os

import streamlit as st

from src.ops.ensure_vector_store import ensure_vector_store
from src.rag.pipeline import ChatResult, answer_question
from src.rag.retriever import ReviewRetriever


@st.cache_resource(show_spinner="Loading embedding model…")
def _get_embedder_store() -> ReviewRetriever:
    return ReviewRetriever()


def _ensure_store_once() -> dict:
    if st.session_state.get("vector_store_ready"):
        return st.session_state.get("vector_store_status", {})
    with st.spinner("Checking search index…"):
        status = ensure_vector_store()
    st.session_state.vector_store_ready = True
    st.session_state.vector_store_status = status
    return status


def _sources_payload(result: ChatResult) -> list[dict]:
    return [
        {
            "review_id": item.review_id,
            "rating": item.rating,
            "date": item.date,
            "similarity": item.similarity,
            "document": item.document[:400],
        }
        for item in result.retrieved
    ]


def _render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"Source excerpts ({len(sources)} retrieved)"):
        for item in sources:
            st.markdown(
                f"**`{item['review_id']}`** · {item['rating']}★ · {item['date']} "
                f"· similarity {item['similarity']:.2f}"
            )
            doc = item["document"]
            st.caption(doc + ("…" if len(doc) >= 400 else ""))
            st.divider()


def render_chatbot() -> None:
    st.subheader("Chatbot")
    st.caption(
        "Ask about music discovery and recommendations. Answers use Groq when available, "
        "with retrieval-only fallback so you always get cited excerpts."
    )

    status = _ensure_store_once()
    if status.get("action") == "rebuilt":
        st.success(
            f"Built search index: {status.get('count', 0):,} reviews "
            f"({status.get('duration_seconds', '?')}s)."
        )

    retriever = _get_embedder_store()
    st.caption(f"Vector store: **{retriever.corpus_size:,}** embedded reviews")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                _render_sources(msg["sources"])

    if prompt := st.chat_input("Ask about discovery, recommendations, shuffle, playlists…"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Searching reviews…"):
                result = answer_question(prompt, retriever)

            st.markdown(result.answer)
            sources = _sources_payload(result)
            _render_sources(sources)

            if result.meta.get("fallback"):
                st.caption(f"Retrieval fallback ({result.meta.get('fallback_reason', 'n/a')})")
            elif result.groq_called:
                st.caption(
                    f"Groq: {result.meta.get('model', 'n/a')} · "
                    f"similarity {result.max_similarity:.2f}"
                )
            elif result.refused:
                st.caption(
                    f"Refused · similarity {result.max_similarity:.2f} "
                    f"(threshold {os.getenv('RAG_SIMILARITY_THRESHOLD', '0.35')})"
                )

        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": result.answer,
                "sources": sources,
            }
        )

    if st.session_state.chat_messages and st.button("Clear chat", key="clear_chat"):
        st.session_state.chat_messages = []
        st.rerun()
