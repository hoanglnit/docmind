from __future__ import annotations
import logging
from typing import Optional, List
from openai import AsyncOpenAI
from .config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=settings.ollama_base_url,
            api_key="ollama",  # Ollama yêu cầu field này nhưng không validate giá trị
        )
    return _client


async def stream_chat(messages: List[dict], temperature: float = 0.7, max_tokens: int = 2048):
    client = get_client()
    try:
        stream = await client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error("LLM streaming error: %s", e)
        yield f"\n[Lỗi kết nối đến Ollama: {e}]"


async def check_health() -> dict:
    client = get_client()
    try:
        models = await client.models.list()
        return {"ok": True, "models": [m.id for m in models.data]}
    except Exception as e:
        return {"ok": False, "error": str(e)}
