"""Text similarity utilities for hallucination detection.

Uses sentence-transformers/all-MiniLM-L6-v2 for semantic similarity.
The model is loaded lazily in a thread pool executor so it never blocks
the asyncio event loop.
"""

import asyncio
import re
import logging
from functools import partial
from typing import Optional

logger = logging.getLogger(__name__)

# Module-level cache for the loaded model
_model = None


def _load_model_sync():
    """Synchronous model loader — runs in a thread pool, not the event loop."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Model loaded.")
        except Exception as e:
            logger.warning(f"sentence-transformers unavailable: {e}. Using keyword similarity.")
    return _model


async def _get_model_async():
    """Async model getter — loads in executor so event loop stays unblocked."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _load_model_sync)


def cosine_similarity(v1, v2) -> float:
    """Compute cosine similarity between two vectors."""
    try:
        import numpy as np
        a = np.array(v1)
        b = np.array(v2)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    except Exception:
        return 0.0


async def semantic_similarity(text1: str, text2: str) -> float:
    """Async semantic similarity using sentence-transformers. Returns 0.0–1.0.

    Falls back to keyword overlap if the model cannot be loaded.
    Runs model.encode() in a thread pool executor to avoid blocking the event loop.
    """
    try:
        model = await _get_model_async()
        if model is None:
            return keyword_similarity(text1, text2)
        loop = asyncio.get_event_loop()
        encode_fn = partial(model.encode, [text1, text2], convert_to_tensor=False)
        embeddings = await loop.run_in_executor(None, encode_fn)
        return cosine_similarity(embeddings[0].tolist(), embeddings[1].tolist())
    except Exception:
        return keyword_similarity(text1, text2)


def keyword_similarity(text1: str, text2: str) -> float:
    """Simple keyword overlap similarity as a fallback."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)


def extract_numbers(text: str) -> list[str]:
    """Extract all numeric values from text, including currency and percentages."""
    # Matches: $2.3M, 1,450, 12%, 3.14, etc.
    pattern = r'\$?[\d,]+\.?\d*[MBKk%]?'
    return re.findall(pattern, str(text))


def normalize_number(n: str) -> Optional[float]:
    """Normalize a number string to a float for comparison."""
    try:
        n = n.strip().lstrip('$').rstrip('%')
        multiplier = 1.0
        if n.endswith('M'):
            multiplier = 1_000_000
            n = n[:-1]
        elif n.endswith('B'):
            multiplier = 1_000_000_000
            n = n[:-1]
        elif n.endswith('K') or n.endswith('k'):
            multiplier = 1_000
            n = n[:-1]
        n = n.replace(',', '')
        return float(n) * multiplier
    except (ValueError, AttributeError):
        return None
