"""Employee Onboarding Agent - Streamlit UI.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import streamlit as st

import config
from agent.graph import NO_ANSWER, build_graph, renumber_citations, stream_turn, usage_cost
from agent.retriever import KBRetriever, is_relevant
from ui_background import BACKGROUNDS, CONTENT_KEY, DEFAULT_BACKGROUND, apply_background

st.set_page_config(page_title="Employee Onboarding Agent", page_icon=":material/badge:")

STARTER_QUESTIONS = [
    "How many vacation days do I get per year?",
    "How do I report a sick day?",
    "When is payday?",
    "How do I set up multi-factor authentication?",
]


@st.cache_resource(show_spinner="Loading knowledge base...")
def get_agent():
    retriever = KBRetriever()
    return retriever, build_graph(retriever)


def log_feedback(index: int) -> None:
    msg = st.session_state.messages[index]
    score = st.session_state.get(f"fb_{st.session_state.thread_id}_{index}")
    if score is None:
        return
    config.FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "thread_id": st.session_state.thread_id,
        "question": msg["question"],
        "answer": msg["content"],
        "citations": [c["ticket_id"] for c in msg["citations"]],
        "rating": "up" if score == 1 else "down",
    }
    with open(config.FEEDBACK_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    st.toast("Thanks for the feedback!")


def render_sources(citations: list[dict]) -> None:
    if not citations:
        return
    with st.expander(f"Sources ({len(citations)})"):
        for i, c in enumerate(citations, start=1):
            st.markdown(
                f"**[{i}] {c['title']}**  \n"
                f":gray[{c['ticket_id']} · {c['category']} · updated {c['updated_date'][:10]}]"
            )
            st.caption(c["content"])


def render_debug(debug: dict) -> None:
    with st.expander("Debug", icon=":material/bug_report:"):
        st.markdown(f"**Standalone query:** {debug['standalone_query']}")
        st.markdown(f"**Graph path:** {' → '.join(debug['trace'])}")
        st.markdown(
            f"**Retrieval** ({config.RETRIEVAL_MODE}; kept if similarity ≥ {config.MIN_SIMILARITY}"
            + (f" or BM25 ≥ {config.MIN_BM25_SCORE}" if config.RETRIEVAL_MODE == "hybrid" else "")
            + "):"
        )
        st.dataframe(
            [
                {"ticket_id": c["ticket_id"], "title": c["title"], "similarity": c["similarity"],
                 "bm25": c["bm25"], "score": c["score"], "kept": is_relevant(c)}
                for c in debug["candidates"]
            ],
            hide_index=True,
        )
        usage = debug.get("usage", [])
        tin, tout, cost = usage_cost(usage)
        st.markdown(
            f"**OpenAI usage** (`{config.OPENAI_MODEL}`): {tin:,} input + {tout:,} output tokens "
            f"· est. ${cost:.5f}"
        )
        if usage:
            st.dataframe(
                [{"call": u["node"], "input tokens": u["input"], "output tokens": u["output"]} for u in usage],
                hide_index=True,
            )
        else:
            st.caption("No chat-model calls this turn (answered by the fallback without generation).")


def session_usage() -> list[dict]:
    return [u for m in st.session_state.messages for u in (m.get("debug") or {}).get("usage", [])]


# ---- Session state -------------------------------------------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []

# ---- Sidebar -------------------------------------------------------------------
with st.sidebar:
    st.header("Onboarding Agent")
    if st.button("New chat", icon=":material/add:", width="stretch"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    show_debug = st.toggle("Show debug panel", value=False)
    if show_debug:
        tin, tout, cost = usage_cost(session_usage())
        st.metric("This chat: est. cost", f"${cost:.4f}", help="Chat-model tokens only; "
                  "query embeddings (text-embedding-3-small) add a negligible amount.")
        st.caption(f"{tin:,} input + {tout:,} output tokens")
    st.caption(f"Model: `{config.OPENAI_MODEL}` (OpenAI)  \nEmbeddings: `{config.EMBEDDING_MODEL}`")
    background = st.segmented_control(
        "Background", list(BACKGROUNDS), default=DEFAULT_BACKGROUND, key="background",
    ) or DEFAULT_BACKGROUND
apply_background(background)

if not config.OPENAI_API_KEY:
    st.error(
        "**OPENAI_API_KEY is not set.** Copy `.env.example` to `.env`, add your OpenAI API key, "
        "and restart the app."
    )
    st.stop()

try:
    retriever, graph = get_agent()
except Exception as exc:  # e.g. invalid key or no network while embedding the KB
    st.error(f"Could not build the knowledge-base index ({type(exc).__name__}: {exc}).")
    st.stop()
with st.sidebar:
    st.caption(f"{retriever.count()} published knowledge-base entries indexed")

# Main content sits in a frosted panel (styled in ui_background) over the landscape.
panel = st.container(key=CONTENT_KEY)
with panel:
    st.title("Employee Onboarding Agent")
    st.caption("Ask anything about the organization. Answers come from the employee knowledge base.")

    # ---- Chat history ----------------------------------------------------------
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                render_sources(msg["citations"])
                if show_debug and msg.get("debug"):
                    render_debug(msg["debug"])
                st.feedback("thumbs", key=f"fb_{st.session_state.thread_id}_{i}",
                            on_change=log_feedback, args=(i,))

    # ---- Starter questions (empty chat only) -----------------------------------
    starter = None
    if not st.session_state.messages:
        st.markdown("**Try asking:**")
        cols = st.columns(2)
        for j, q in enumerate(STARTER_QUESTIONS):
            if cols[j % 2].button(q, key=f"starter_{j}", width="stretch"):
                starter = q

# ---- New question --------------------------------------------------------------
question = st.chat_input("Ask a question about the organization...") or starter
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with panel, st.chat_message("user"):
        st.markdown(question)
    with panel, st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown(":gray[Searching the knowledge base…]")
        docs, buf, result = [], "", None
        try:
            for kind, data in stream_turn(graph, question, st.session_state.thread_id):
                if kind == "docs":
                    docs = data
                elif kind == "token":
                    buf += data
                    shown = buf.lstrip()
                    # Hold back output while it could still be the NO_ANSWER sentinel.
                    if NO_ANSWER.startswith(shown) or shown.startswith(NO_ANSWER):
                        continue
                    # Renumber citations live, so markers match the final Sources list.
                    placeholder.markdown(renumber_citations(buf, docs)[0] + " ▌")
                else:
                    result = data
        except Exception as exc:  # e.g. invalid API key, rate limit, network error
            st.session_state.messages.pop()
            placeholder.error(
                f"The OpenAI API call failed ({type(exc).__name__}: {exc}).  \n"
                "Check your OPENAI_API_KEY, account quota and network connection, then try again."
            )
            st.stop()
    st.session_state.messages.append(
        {
            "role": "assistant",
            "question": question,
            "content": result["answer"],
            "citations": result["citations"],
            "debug": {
                "standalone_query": result["standalone_query"],
                "trace": result["trace"],
                "candidates": result["candidates"],
                "usage": result.get("usage", []),
            },
        }
    )
    st.rerun()
