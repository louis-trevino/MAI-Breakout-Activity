"""Retrieval and citation tests.

Citation tests run offline. Retrieval tests call the OpenAI embeddings API
(a fraction of a cent) and are skipped when OPENAI_API_KEY is not set.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config  # noqa: E402
from agent.graph import renumber_citations, usage_cost  # noqa: E402
from agent.retriever import KBRetriever, load_kb  # noqa: E402

EXPECTED = {
    "How many vacation days do I get per year?": "TKT-00003",
    "How do I report a sick day?": "TKT-00004",
    "When do we get paid?": "TKT-00005",
    "How do I change my bank account for direct deposit?": "TKT-00006",
}


@unittest.skipUnless(config.OPENAI_API_KEY, "OPENAI_API_KEY not set")
class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)  # Chroma locks files on Windows
        cls.retriever = KBRetriever(persist_dir=Path(cls.tmp.name))

    def test_only_published_indexed(self):
        self.assertEqual(self.retriever.count(), len(load_kb()))
        self.assertTrue(all(e["metadata"]["status"] == "published" for e in load_kb()))

    def test_expected_ticket_in_top_k_above_threshold(self):
        for question, ticket in EXPECTED.items():
            with self.subTest(question=question):
                hits = self.retriever.search(question)
                self.assertLessEqual(len(hits), config.TOP_K)
                kept = [h.ticket_id for h in hits if h.relevant]
                self.assertIn(ticket, kept)

    def test_keyword_only_match_is_kept(self):
        # Vector similarity alone is below the threshold here; BM25 rescues it.
        hits = self.retriever.search("PD missing on order")
        self.assertEqual(hits[0].ticket_id, "TKT-00018")
        self.assertTrue(hits[0].relevant)

    def test_pending_ticket_never_returned(self):
        hits = self.retriever.search("How to request a vacation")
        self.assertNotIn("TKT-00002", [h.ticket_id for h in hits])

    def test_off_topic_below_threshold(self):
        hits = self.retriever.search("What is the capital of Mongolia?")
        self.assertFalse(any(h.relevant for h in hits),
                         [(h.ticket_id, h.similarity, h.bm25) for h in hits])


class CitationTests(unittest.TestCase):
    docs = [{"ticket_id": f"T{i}"} for i in range(1, 6)]

    def test_renumbers_in_order_of_appearance(self):
        text, cites = renumber_citations("A [3]. B [1][3]. C [9].", self.docs)
        self.assertEqual(text, "A [1]. B [2][1]. C .")
        self.assertEqual([c["ticket_id"] for c in cites], ["T3", "T1"])

    def test_no_markers(self):
        self.assertEqual(renumber_citations("plain", self.docs), ("plain", []))


class UsageCostTests(unittest.TestCase):
    def test_cost_uses_model_prices(self):
        usage = [{"node": "condense_query", "input": 1_000_000, "output": 0},
                 {"node": "generate", "input": 0, "output": 1_000_000}]
        tin, tout, cost = usage_cost(usage)
        p_in, p_out = config.model_prices()
        self.assertEqual((tin, tout), (1_000_000, 1_000_000))
        self.assertAlmostEqual(cost, p_in + p_out)

    def test_empty_usage(self):
        self.assertEqual(usage_cost([]), (0, 0, 0.0))


if __name__ == "__main__":
    unittest.main()
