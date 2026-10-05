from fastapi import APIRouter
from .. import llm_client, vector_store
from ..services import embedding_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    ollama_status = await llm_client.check_health()
    return {
        "status": "ok",
        "ollama": ollama_status,
        "chromadb": vector_store.is_ready(),
        "embedding_model": embedding_service.is_loaded(),
    }
