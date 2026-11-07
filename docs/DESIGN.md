# Employee Onboarding Agent: Design

By MAI Team 31

Luis Carvajal Trevino, Aditi Jalota, Peyvand, Shilpa Srihari, Akshay Jain, Shreya Ramesh

## Purpose

New employees ask questions about the organization in a chat UI. The agent answers only from the employee knowledge base (`kb_employee_sample_01.json`), cites at most 5 sources, and keeps the conversation going across follow-up questions.

## Decisions

| Area | Decision | Rationale |
|---|---|---|
| Frontend | Streamlit chat (`st.chat_input`, `st.chat_message`) | Required stack; native chat widgets |
| Orchestration | LangGraph `StateGraph` | Explicit, inspectable steps; easy to add tools/nodes later |
| LLM | OpenAI `gpt-4.1-mini` via `langchain-openai`, temperature 0 | Low cost, reliable at citation and `NO_ANSWER` instructions. Replaced local Ollama, which needed about 5 GB of disk and more RAM than the 8 GB laptop had free |
| Embeddings | OpenAI `text-embedding-3-small` | No local PyTorch (saves about 1 GB). Embedding 22 entries costs a fraction of a cent |
| Secrets | `OPENAI_API_KEY` from the environment or a git-ignored `.env` (`python-dotenv`) | The key is never in code or the repo |
| Vector store | ChromaDB (persistent, cosine) in `.chroma/` | Local, supports metadata filters |
| Retrieval | Hybrid: BM25 keyword + vector, fused with Reciprocal Rank Fusion | Exact terms ("PD", "Tier 2", "stipend") that vector-only search scored below threshold. Eval with the earlier local embeddings: 29/31 vs 26/31 |
| KB scope | `status == "published"` only (22 of 26 entries); all categories | Unreviewed (pending/draft) and archived content is never cited |
| Language | English only | One Spanish entry exists but is low priority |
| Unanswerable | Fixed decline message suggesting manager or HR, no citations | No made-up policy answers |
| Memory | Per browser session (`st.session_state` + LangGraph `MemorySaver`) | Simple, and nothing personal is stored |

## Knowledge base

- Short entries (≤ 335 chars), so each entry is one chunk and no splitting is needed.
- The embedded text is `title + ". " + content`. The title improves matches for very short entries.
- Metadata stored with each vector: `ticket_id`, `title`, `category`, `status`, `updated_date`, `content`.
- The index is rebuilt automatically when the KB file, the embedding model or the status filter changes (a fingerprint is stored in the collection metadata).

## Agent graph

```
START → condense_query → retrieve → check_relevance ─┬─ docs found ─→ generate ─→ END
                                                     └─ none ───────→ fallback ─→ END
```

| Node | What it does |
|---|---|
| `condense_query` | Rewrites a follow-up into a standalone question using the last `HISTORY_TURNS` messages. Skipped on the first turn. |
| `retrieve` | Scores every published entry with both cosine similarity (Chroma, filter `status ∈ ALLOWED_STATUSES`) and BM25 (stopwords removed). Ranks by RRF (`1/(60+rank_vec) + 1/(60+rank_bm25)`), relevant entries first, and keeps the top `TOP_K=5`. |
| `check_relevance` | Keeps an entry if similarity ≥ `MIN_SIMILARITY` (0.40) **or** BM25 ≥ `MIN_BM25_SCORE` (4.0). Both were tuned for `text-embedding-3-small` with `eval/run_eval.py retrieval`. A score threshold is cheap, deterministic and easy to debug. |
| `generate` | Numbered sources go in the system prompt. The model must cite as `[n]`, or reply `NO_ANSWER`. Citations are then filtered to the sources actually cited and renumbered 1..n. If the model cites nothing, all relevant docs are shown. |
| `fallback` | Returns `FALLBACK_MESSAGE` with no citations. Also used when `generate` returns `NO_ANSWER`. |

State: `messages` (persisted, `add_messages` reducer), `question`, `standalone_query`, `candidates`, `docs`, `answer`, `citations`, `trace`, `usage` (tokens per LLM call this turn).

**Streaming:** `stream_turn()` runs the graph with `stream_mode=["updates", "messages"]`. It yields the relevant sources as soon as `check_relevance` finishes, then the `generate` node's tokens as they arrive, then the final state. The UI renumbers citations live (so `[n]` already matches the Sources list), and holds output while it could still be the `NO_ANSWER` sentinel so that never flashes on screen. `ask()` (non-streaming) is still used by the evaluation harness.

## UI

- Chat history with the answer and inline `[n]` markers. A **Sources** expander lists ticket ID, title, category, updated date and the entry text.
- Sidebar: **New chat** (new thread ID, history cleared), **Show debug panel** toggle, model info and the number of indexed entries.
- An empty chat shows clickable **starter questions**.
- **Thumbs feedback** on every answer, appended to `logs/feedback.jsonl` (question, answer, cited ticket IDs, rating).
- Answers **stream** in word by word. The first text appears about 2 s after the question.
- The **Debug panel** shows:
  - the standalone query, the graph path, and every retrieval candidate with its similarity, BM25 score and whether it was kept
  - **OpenAI usage** per answer: input and output tokens per call (`condense_query`, `generate`) and the estimated cost
  - with debug on, the sidebar also shows the **estimated cost of the current chat**.
- Cost estimates use `MODEL_PRICES` in `config.py` (USD per 1M tokens). Check them against current OpenAI pricing; they can be overridden with `PRICE_INPUT_PER_M` and `PRICE_OUTPUT_PER_M`. Query embeddings are not counted (negligible). A typical answer is about 300–600 tokens, roughly $0.0002–0.0003 with `gpt-4.1-mini`.
- If `OPENAI_API_KEY` is missing, or an OpenAI call fails (invalid key, quota, network), a clear error is shown in place of a stack trace.

## Configuration

All settings are in `config.py` and can be overridden with environment variables or `.env`: `OPENAI_API_KEY`, `OPENAI_MODEL`, `EMBEDDING_MODEL`, `RETRIEVAL_MODE` (`hybrid`/`vector`), `TOP_K`, `MIN_SIMILARITY`, `MIN_BM25_SCORE`, `RRF_K`, `HISTORY_TURNS`, `PRICE_INPUT_PER_M`, `PRICE_OUTPUT_PER_M`, `KB_PATH`, `CHROMA_DIR`, `FEEDBACK_LOG`.

## Evaluation

`eval/eval_set.json` has 35 cases: 25 answerable, 3 multi-turn follow-ups, 6 that should get the fallback (off-topic, or answered only by archived/pending entries), and 1 informational case.

- `python eval/run_eval.py retrieval -v`: compares vector and hybrid retrieval across a threshold sweep. Uses embeddings only, no chat model.
- `python eval/run_eval.py e2e`: runs the full agent and writes `eval/report_e2e.md` with every answer.

**Results (2026-11-06, `gpt-4.1-mini` + `text-embedding-3-small`, hybrid, 0.40 / 4.0):**

- Retrieval: all 25 answerable questions find the right entry. 4 of 6 unanswerable questions retrieve nothing; the other 2 retrieve related entries, and the LLM's `NO_ANSWER` rule catches them.
- End to end: **34/34 pass**. Every answer cites the right entry, follow-ups are rewritten correctly, and all 6 unanswerable questions get the fallback. Average about 1.2 s per question (about 3 s for follow-ups, which need an extra rewrite call).

Known KB gap: the only *published* entry on requesting vacation is the Spanish TKT-00026. The English TKT-00002 is still pending.

## Test plan

1. **Retrieval** (`tests/test_retrieval.py`, embeddings API only; skipped without a key): sample questions return the expected ticket in the top 5 above the threshold, non-published tickets are never returned, and an off-topic question falls below the threshold.
2. **Citation post-processing**: unit tests for `renumber_citations`.
3. **End to end** (needs `OPENAI_API_KEY`): a single question, a follow-up ("what about carryover?" after a vacation question), an off-topic question that should trigger the fallback, and a check that there are at most 5 citations.
4. **Feedback**: review `logs/feedback.jsonl` to tune `MIN_SIMILARITY` and the prompts.

## Possible next steps

- SQLite checkpointer and SSO for conversations that persist.
- Tools (e.g. "open an HR ticket") as extra graph nodes.
