r"""LangGraph definition of the Employee Onboarding Agent.

    START -> condense_query -> retrieve -> check_relevance --(relevant)--> generate -> END
                                                           \--(none)-----> fallback -> END
"""
from __future__ import annotations

import re
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

import config
from agent.prompts import ANSWER_SYSTEM_PROMPT, CONDENSE_PROMPT
from agent.retriever import KBRetriever, is_relevant

CITATION_RE = re.compile(r"\[(\d+)\]")
NO_ANSWER = "NO_ANSWER"


class AgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]  # full chat history (persisted)
    question: str  # raw user question for this turn
    standalone_query: str  # rewritten question used for retrieval
    candidates: list[dict]  # top-k from the vector store, with scores
    docs: list[dict]  # candidates that passed the relevance threshold
    answer: str
    citations: list[dict]  # sources actually cited, renumbered 1..n
    trace: list[str]  # node path taken this turn (debug panel)
    usage: list[dict]  # token usage per LLM call this turn: {node, input, output}


def _usage(node: str, msg) -> dict:
    u = getattr(msg, "usage_metadata", None) or {}
    return {"node": node, "input": u.get("input_tokens", 0), "output": u.get("output_tokens", 0)}


def usage_cost(usage: list[dict]) -> tuple[int, int, float]:
    """(input tokens, output tokens, estimated USD) for a list of usage records."""
    tin = sum(u["input"] for u in usage)
    tout = sum(u["output"] for u in usage)
    p_in, p_out = config.model_prices()
    return tin, tout, (tin * p_in + tout * p_out) / 1_000_000


def _format_history(messages: list[BaseMessage]) -> str:
    lines = []
    for m in messages:
        role = "Employee" if isinstance(m, HumanMessage) else "Assistant"
        lines.append(f"{role}: {CITATION_RE.sub('', str(m.content)).strip()}")
    return "\n".join(lines)


def renumber_citations(answer: str, docs: list[dict]) -> tuple[str, list[dict]]:
    """Keep only cited sources and renumber them 1..n in order of first appearance."""
    order: list[int] = []
    for m in CITATION_RE.finditer(answer):
        n = int(m.group(1))
        if 1 <= n <= len(docs) and n not in order:
            order.append(n)
    if not order:
        return answer, []
    mapping = {old: new for new, old in enumerate(order, start=1)}

    def _sub(m: re.Match) -> str:
        n = int(m.group(1))
        return f"[{mapping[n]}]" if n in mapping else ""  # drop invalid markers

    return CITATION_RE.sub(_sub, answer), [docs[i - 1] for i in order]


def build_graph(retriever: KBRetriever, llm: BaseChatModel | None = None, checkpointer=None):
    llm = llm or ChatOpenAI(
        model=config.OPENAI_MODEL, api_key=config.OPENAI_API_KEY, temperature=0, max_retries=2,
        stream_usage=True,  # report token usage even when LangGraph streams the call
    )

    def condense_query(state: AgentState) -> dict:
        history = state["messages"][:-1][-config.HISTORY_TURNS :]
        question = state["question"]
        if not history:
            return {"standalone_query": question, "trace": ["condense_query (skipped)"], "usage": []}
        prompt = CONDENSE_PROMPT.format(history=_format_history(history), question=question)
        resp = llm.invoke(prompt)
        lines = str(resp.content).strip().strip('"').splitlines()
        return {
            "standalone_query": (lines[0].strip() if lines else "") or question,
            "trace": ["condense_query"],
            "usage": [_usage("condense_query", resp)],
        }

    def retrieve(state: AgentState) -> dict:
        hits = retriever.search(state["standalone_query"], k=config.TOP_K)
        return {"candidates": [h.to_dict() for h in hits], "trace": state["trace"] + ["retrieve"]}

    def check_relevance(state: AgentState) -> dict:
        docs = [d for d in state["candidates"] if is_relevant(d)]
        return {"docs": docs, "trace": state["trace"] + ["check_relevance"]}

    def route(state: AgentState) -> str:
        return "generate" if state["docs"] else "fallback"

    def generate(state: AgentState) -> dict:
        docs = state["docs"]
        sources = "\n\n".join(
            f"[{i}] {d['title']} ({d['ticket_id']})\n{d['content']}"
            for i, d in enumerate(docs, start=1)
        )
        history = state["messages"][:-1][-config.HISTORY_TURNS :]
        msgs = [SystemMessage(ANSWER_SYSTEM_PROMPT.format(sources=sources)), *history,
                HumanMessage(state["question"])]
        resp = llm.invoke(msgs)
        raw = str(resp.content).strip()
        usage = state.get("usage", []) + [_usage("generate", resp)]

        if raw.startswith(NO_ANSWER) or not raw:
            return _fallback(state, "generate -> NO_ANSWER", usage)

        answer, citations = renumber_citations(raw, docs)
        if not citations:
            # Model answered but forgot markers: show the relevant docs as sources.
            citations = docs
        return {
            "answer": answer,
            "citations": citations,
            "messages": [AIMessage(answer)],
            "trace": state["trace"] + ["generate"],
            "usage": usage,
        }

    def _fallback(state: AgentState, label: str, usage: list[dict] | None = None) -> dict:
        return {
            "answer": config.FALLBACK_MESSAGE,
            "citations": [],
            "messages": [AIMessage(config.FALLBACK_MESSAGE)],
            "trace": state["trace"] + [label],
            "usage": usage if usage is not None else state.get("usage", []),
        }

    def fallback(state: AgentState) -> dict:
        return _fallback(state, "fallback")

    g = StateGraph(AgentState)
    g.add_node("condense_query", condense_query)
    g.add_node("retrieve", retrieve)
    g.add_node("check_relevance", check_relevance)
    g.add_node("generate", generate)
    g.add_node("fallback", fallback)
    g.add_edge(START, "condense_query")
    g.add_edge("condense_query", "retrieve")
    g.add_edge("retrieve", "check_relevance")
    g.add_conditional_edges("check_relevance", route, {"generate": "generate", "fallback": "fallback"})
    g.add_edge("generate", END)
    g.add_edge("fallback", END)
    return g.compile(checkpointer=checkpointer or MemorySaver())


def _turn_input(question: str) -> dict:
    return {"messages": [HumanMessage(question)], "question": question}


def ask(graph, question: str, thread_id: str) -> AgentState:
    """Run one conversational turn and return the final state."""
    return graph.invoke(_turn_input(question), config={"configurable": {"thread_id": thread_id}})


def stream_turn(graph, question: str, thread_id: str):
    """Run one turn, yielding events as they happen:

    ("docs", list[dict])  relevant sources, once retrieval is done
    ("token", str)        answer text chunks from the `generate` node
    ("final", AgentState) final state, always last
    """
    cfg = {"configurable": {"thread_id": thread_id}}
    for mode, data in graph.stream(_turn_input(question), config=cfg, stream_mode=["updates", "messages"]):
        if mode == "updates":
            update = data.get("check_relevance")
            if update:
                yield "docs", update["docs"]
        else:
            chunk, meta = data
            if meta.get("langgraph_node") == "generate" and chunk.content:
                yield "token", chunk.content
    yield "final", graph.get_state(cfg).values
