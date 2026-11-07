"""Knowledge-base loading, indexing (ChromaDB + BM25) and hybrid retrieval."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from rank_bm25 import BM25Okapi

import config

STOPWORDS = set(
    "a an and are as at be by can do does for from get got have how i if in into is it its "
    "me my of on or our should so than that the their them then there these they this to "
    "up us was we what when where which who why will with you your".split()
)
TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


@dataclass
class RetrievedDoc:
    ticket_id: str
    title: str
    category: str
    updated_date: str
    content: str
    similarity: float  # cosine similarity from the vector search (0..1)
    bm25: float = 0.0  # BM25 keyword score (0 = no shared keywords)
    score: float = 0.0  # final ranking score (RRF in hybrid mode, similarity in vector mode)

    @property
    def relevant(self) -> bool:
        return is_relevant(asdict(self))

    def to_dict(self) -> dict:
        return asdict(self)


def is_relevant(doc: dict) -> bool:
    if doc["similarity"] >= config.MIN_SIMILARITY:
        return True
    return config.RETRIEVAL_MODE == "hybrid" and doc.get("bm25", 0.0) >= config.MIN_BM25_SCORE


def load_kb(path: Path = config.KB_PATH) -> list[dict]:
    """Load the KB and keep only entries whose status is allowed."""
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    return [e for e in entries if e["metadata"].get("status") in config.ALLOWED_STATUSES]


def _doc_text(entry: dict) -> str:
    # Title is prepended so short entries still match on their topic.
    return f'{entry["metadata"]["title"]}. {entry["content"]}'


def _fingerprint(path: Path) -> str:
    """Hash of the KB file + settings, so the index rebuilds when either changes."""
    h = hashlib.sha256(path.read_bytes())
    h.update(config.EMBEDDING_MODEL.encode())
    h.update(",".join(sorted(config.ALLOWED_STATUSES)).encode())
    return h.hexdigest()[:16]


class KBRetriever:
    def __init__(self, kb_path: Path = config.KB_PATH, persist_dir: Path = config.CHROMA_DIR):
        self.kb_path = Path(kb_path)
        self.entries = load_kb(self.kb_path)
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.")
        self.embed_fn = OpenAIEmbeddingFunction(
            api_key=config.OPENAI_API_KEY, model_name=config.EMBEDDING_MODEL
        )
        self.collection = self._get_or_build()
        # BM25 is tiny for this KB, so it is rebuilt in memory on startup.
        self.bm25 = BM25Okapi([tokenize(_doc_text(e)) for e in self.entries])

    def _get_or_build(self):
        fp = _fingerprint(self.kb_path)
        try:
            col = self.client.get_collection(config.COLLECTION_NAME, embedding_function=self.embed_fn)
            if (col.metadata or {}).get("fingerprint") == fp:
                return col
        except Exception:
            pass  # missing, or built with a different embedding function
        try:
            self.client.delete_collection(config.COLLECTION_NAME)  # stale index
        except Exception:
            pass

        col = self.client.create_collection(
            config.COLLECTION_NAME,
            embedding_function=self.embed_fn,
            metadata={"hnsw:space": "cosine", "fingerprint": fp},
        )
        col.add(
            ids=[e["metadata"]["ticket_id"] for e in self.entries],
            documents=[_doc_text(e) for e in self.entries],
            metadatas=[
                {
                    "ticket_id": e["metadata"]["ticket_id"],
                    "title": e["metadata"]["title"],
                    "category": e["metadata"]["category"],
                    "status": e["metadata"]["status"],
                    "updated_date": e["metadata"]["updated_date"],
                    "content": e["content"],
                }
                for e in self.entries
            ],
        )
        return col

    def count(self) -> int:
        return self.collection.count()

    def _vector_scores(self, query: str) -> dict[str, tuple[float, dict]]:
        """ticket_id -> (cosine similarity, metadata) for every indexed entry."""
        res = self.collection.query(
            query_texts=[query],
            n_results=self.count(),  # KB is small: score everything, then fuse
            where={"status": {"$in": sorted(config.ALLOWED_STATUSES)}},
        )
        return {
            meta["ticket_id"]: (round(1.0 - dist, 4), meta)
            for meta, dist in zip(res["metadatas"][0], res["distances"][0])
        }

    def search(self, query: str, k: int = config.TOP_K) -> list[RetrievedDoc]:
        """Top-k entries for the query, best first (relevance threshold NOT applied)."""
        vec = self._vector_scores(query)
        bm25_raw = self.bm25.get_scores(tokenize(query))
        bm25 = {e["metadata"]["ticket_id"]: round(float(s), 4) for e, s in zip(self.entries, bm25_raw)}

        docs = []
        for tid, (sim, meta) in vec.items():
            docs.append(
                RetrievedDoc(
                    ticket_id=tid,
                    title=meta["title"],
                    category=meta["category"],
                    updated_date=meta["updated_date"],
                    content=meta["content"],
                    similarity=sim,
                    bm25=bm25.get(tid, 0.0),
                )
            )

        if config.RETRIEVAL_MODE == "hybrid":
            vec_rank = {d.ticket_id: r for r, d in enumerate(sorted(docs, key=lambda d: -d.similarity), 1)}
            kw_hits = sorted((d for d in docs if d.bm25 > 0), key=lambda d: -d.bm25)
            kw_rank = {d.ticket_id: r for r, d in enumerate(kw_hits, 1)}
            for d in docs:
                d.score = 1 / (config.RRF_K + vec_rank[d.ticket_id])
                if d.ticket_id in kw_rank:
                    d.score += 1 / (config.RRF_K + kw_rank[d.ticket_id])
                d.score = round(d.score, 5)
        else:
            for d in docs:
                d.score = d.similarity

        # Relevant entries first, so a strong match on only one signal is never cut by k.
        docs.sort(key=lambda d: (not d.relevant, -d.score))
        return docs[:k]
