"""Text similarity utilities for hallucination detection.

Uses sentence-transformers/all-MiniLM-L6-v2 for semantic similarity.
The model is loaded lazily on first use to avoid slow server startup.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Module-level cache for the loaded model
_model = None


def get_model():
    """Lazily load and cache the sentence-transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load sentence-transformers model: {e}. Falling back to keyword similarity.")
            _model = None
    return _model


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
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


def semantic_similarity(text1: str, text2: str) -> float:
    """Compute semantic similarity between two texts. Returns 0.0–1.0.

    Uses keyword overlap as a fast, non-blocking fallback. Sentence-transformers
    (all-MiniLM-L6-v2) can be enabled by calling get_model() explicitly, but it
    spawns PyTorch threads that block the asyncio event loop on low-resource hosts.
    """
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
