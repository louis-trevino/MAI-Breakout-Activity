"""Evaluation harness for the Employee Onboarding Agent.

  python eval/run_eval.py retrieval   # retrieval only (no LLM): vector vs hybrid, threshold sweep
  python eval/run_eval.py e2e         # full agent (OpenAI API); writes eval/report_e2e.md

For multi-turn cases, retrieval mode uses the last turn verbatim (no rewriting),
so follow-up cases are expected to be weak there; e2e mode exercises the rewriter.
"""
from __future__ import annotations

import argparse
import functools
import json
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from agent.retriever import KBRetriever, is_relevant  # noqa: E402

CASES = json.loads((ROOT / "eval" / "eval_set.json").read_text(encoding="utf-8"))


def score_case(case: dict, kept_ids: list[str]) -> bool:
    if not case["expected"]:
        return not kept_ids  # unanswerable: nothing should be kept
    return any(t in kept_ids for t in case["expected"])


def retrieval_eval(retriever: KBRetriever, verbose: bool) -> None:
    single = [c for c in CASES if len(c["turns"]) == 1 and not c.get("informational")]
    # Embed each query once (one API call per query), then sweep thresholds offline.
    retriever._vector_scores = functools.lru_cache(maxsize=None)(retriever._vector_scores)
    sims = (0.25, 0.30, 0.35, 0.40, 0.45, 0.50)
    configs = [("vector", s, None) for s in sims]
    configs += [("hybrid", s, b) for s in sims for b in (3.0, 4.0, 5.0)]

    print(f"{len(single)} single-turn cases\n")
    print(f"{'mode':7} {'sim':>5} {'bm25':>5} | {'answerable':>10} {'unanswerable':>12} {'total':>6} {'avg kept':>8}")
    for mode, sim, bm in configs:
        config.RETRIEVAL_MODE, config.MIN_SIMILARITY = mode, sim
        if bm is not None:
            config.MIN_BM25_SCORE = bm
        ok_a = ok_u = n_a = n_u = kept_total = 0
        failures = []
        for c in single:
            hits = retriever.search(c["turns"][-1])
            kept = [h.ticket_id for h in hits if h.relevant]
            kept_total += len(kept)
            ok = score_case(c, kept)
            if c["expected"]:
                n_a += 1; ok_a += ok
            else:
                n_u += 1; ok_u += ok
            if not ok:
                failures.append((c["id"], [(h.ticket_id, h.similarity, h.bm25) for h in hits[:3]]))
        print(f"{mode:7} {sim:5.2f} {bm if bm is not None else '-':>5} | {ok_a:>4}/{n_a:<5} {ok_u:>6}/{n_u:<5} "
              f"{ok_a + ok_u:>3}/{n_a + n_u:<2} {kept_total / len(single):8.2f}")
        if verbose:
            for f in failures:
                print("     FAIL", f)


def e2e_eval(retriever: KBRetriever) -> None:
    from agent.graph import ask, build_graph

    graph = build_graph(retriever)
    rows, lines = [], [
        f"# E2E evaluation\n",
        f"Model `{config.OPENAI_MODEL}` · embeddings `{config.EMBEDDING_MODEL}` · retrieval `{config.RETRIEVAL_MODE}` · "
        f"MIN_SIMILARITY {config.MIN_SIMILARITY} · MIN_BM25_SCORE {config.MIN_BM25_SCORE}\n",
    ]
    for c in CASES:
        thread = str(uuid.uuid4())
        t0 = time.perf_counter()
        for q in c["turns"]:
            state = ask(graph, q, thread)
        secs = time.perf_counter() - t0
        cited = [x["ticket_id"] for x in state["citations"]]
        fell_back = state["answer"] == config.FALLBACK_MESSAGE
        if c["expected"]:
            ok = (not fell_back) and any(t in cited for t in c["expected"])
        else:
            ok = fell_back
        ok = ok and len(cited) <= config.TOP_K
        rows.append((c, ok, secs))
        flag = "PASS" if ok else ("INFO" if c.get("informational") else "FAIL")
        print(f"[{flag}] {c['id']:26} {secs:5.1f}s cited={cited} path={state['trace'][-1]}")
        lines += [
            f"## [{flag}] {c['id']}",
            *[f"> **Q{i}:** {q}" for i, q in enumerate(c["turns"], 1)],
            f"\nStandalone query: _{state['standalone_query']}_  ",
            f"Expected: {c['expected'] or 'fallback'} · Cited: {cited or '-'} · {secs:.1f}s"
            + (f"  \nNote: {c['note']}" if c.get("note") else ""),
            f"\n{state['answer']}\n",
        ]
    scored = [r for r in rows if not r[0].get("informational")]
    passed = sum(ok for _, ok, _ in scored)
    avg = sum(s for *_, s in rows) / len(rows)
    summary = f"**{passed}/{len(scored)} passed** · avg {avg:.1f}s per case"
    print("\n" + summary)
    lines.insert(2, summary + "\n")
    out = ROOT / "eval" / "report_e2e.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["retrieval", "e2e"])
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    r = KBRetriever()
    retrieval_eval(r, args.verbose) if args.mode == "retrieval" else e2e_eval(r)
