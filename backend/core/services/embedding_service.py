"""Embedding service using Sentence Transformers. Caches model and vectors."""
import logging
from typing import List

from django.conf import settings

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        name = settings.EMBEDDING_CONFIG.get('MODEL_NAME', 'all-MiniLM-L6-v2')
        _model = SentenceTransformer(name)
    return _model


def encode(texts: List[str]) -> List[List[float]]:
    """Batch encode texts to vectors."""
    if not texts:
        return []
    model = _get_model()
    return model.encode(texts, convert_to_numpy=True).tolist()


def encode_single(text: str) -> List[float]:
    """Encode single text."""
    return encode([text])[0] if text else [0.0] * settings.EMBEDDING_CONFIG.get('DIMENSION', 384)
