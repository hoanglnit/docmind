from __future__ import annotations
import logging
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from .config import settings

logger = logging.getLogger(__name__)

_client: Optional[chromadb.PersistentClient] = None
_collection = None
COLLECTION_NAME = "docmind_chunks"


def get_collection():
    global _client, _collection
    if _collection is None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=str(settings.chroma_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection ready: %s", COLLECTION_NAME)
    return _collection


def add_chunks(document_id: str, chunks: List[str], embeddings: List[List[float]], metadatas: List[dict]):
    collection = get_collection()
    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    collection.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)


def query_chunks(query_embedding: List[float], document_ids: List[str], top_k: int = 5) -> List[dict]:
    if not document_ids:
        return []
    collection = get_collection()
    total = collection.count()
    if total == 0:
        return []

    n_results = min(top_k, total)
    where = {"document_id": {"$in": document_ids}} if len(document_ids) > 1 else {"document_id": document_ids[0]}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    if results["documents"] and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            chunks.append({"document": doc, "metadata": meta, "distance": dist})
    return chunks


def delete_document(document_id: str):
    collection = get_collection()
    collection.delete(where={"document_id": document_id})
    logger.info("Deleted ChromaDB chunks for document: %s", document_id)


def is_ready() -> bool:
    try:
        get_collection()
        return True
    except Exception:
        return False
