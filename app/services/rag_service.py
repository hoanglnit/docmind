import asyncio
from . import embedding_service
from .. import vector_store


async def retrieve(query: str, document_ids: list[str], top_k: int = 5) -> list[dict]:
    if not document_ids:
        return []
    query_embedding = await asyncio.to_thread(embedding_service.embed_query, query)
    chunks = await asyncio.to_thread(vector_store.query_chunks, query_embedding, document_ids, top_k)
    return chunks
