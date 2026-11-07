"""Central configuration for the Employee Onboarding Agent.

Every value can be overridden with an environment variable of the same name,
or in a local `.env` file (see `.env.example`).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")  # does not override variables already set in the environment

KB_PATH = Path(os.getenv("KB_PATH", BASE_DIR / "kb_employee_sample_01.json"))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / ".chroma"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "employee_kb")
FEEDBACK_LOG = Path(os.getenv("FEEDBACK_LOG", BASE_DIR / "logs" / "feedback.jsonl"))

# Only entries with these statuses are indexed (pending/draft/archived are excluded).
ALLOWED_STATUSES = {"published"}

# OpenAI (the API key is read from OPENAI_API_KEY; never hard-code it).
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Estimated USD per 1M tokens (input, output), shown in the UI. Check current OpenAI pricing
# and override with PRICE_INPUT_PER_M / PRICE_OUTPUT_PER_M if it differs.
MODEL_PRICES = {
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
    "gpt-4o-mini": (0.15, 0.60),
}


def model_prices() -> tuple[float, float]:
    p_in, p_out = MODEL_PRICES.get(OPENAI_MODEL, (0.0, 0.0))
    return (
        float(os.getenv("PRICE_INPUT_PER_M", p_in)),
        float(os.getenv("PRICE_OUTPUT_PER_M", p_out)),
    )


TOP_K = int(os.getenv("TOP_K", "5"))  # max citations per answer
# "hybrid" = BM25 keyword + vector search fused with Reciprocal Rank Fusion; "vector" = vector only.
RETRIEVAL_MODE = os.getenv("RETRIEVAL_MODE", "hybrid")
RRF_K = int(os.getenv("RRF_K", "60"))  # standard RRF damping constant
# An entry is relevant if EITHER signal clears its threshold:
# cosine similarity (0..1) from the vector search ...
# Tuned for text-embedding-3-small with `python eval/run_eval.py retrieval -v`.
MIN_SIMILARITY = float(os.getenv("MIN_SIMILARITY", "0.40"))
# ... or a BM25 keyword score (exact-term matches such as "VPN", "PD", "Tier 2"). Hybrid mode only.
MIN_BM25_SCORE = float(os.getenv("MIN_BM25_SCORE", "4.0"))  # tuned with eval/run_eval.py retrieval
# How many previous messages are used to rewrite a follow-up question.
HISTORY_TURNS = int(os.getenv("HISTORY_TURNS", "6"))

FALLBACK_MESSAGE = (
    "I couldn't find anything about that in the employee knowledge base. "
    "Please reach out to your manager or the HR team, who can help you directly."
)
