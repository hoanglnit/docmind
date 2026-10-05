from __future__ import annotations
import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from ..config import settings

logger = logging.getLogger(__name__)

_model: Optional[SentenceTransformer] = None


def load_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded")
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = load_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    return embed_texts([query])[0]


def is_loaded() -> bool:
    return _model is not None
