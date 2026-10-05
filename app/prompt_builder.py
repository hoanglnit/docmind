from __future__ import annotations
from typing import List, Optional
from jinja2 import Template
from .models.scenario import Scenario, DEFAULT_SYSTEM_PROMPT
from .models.message import Message


def build_messages(
    scenario: Optional[Scenario],
    chunks: List[dict],
    history: List[Message],
    user_message: str,
    document_names: Optional[List[str]] = None,
) -> List[dict]:
    template_str = scenario.system_prompt if scenario else DEFAULT_SYSTEM_PROMPT
    rendered_system = Template(template_str).render(documents=document_names or [])

    if chunks:
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk["metadata"].get("source", "Unknown")
            page = chunk["metadata"].get("page")
            ref = source + (f" — trang {page}" if page else "")
            context_parts.append(f"[Nguồn {i}: {ref}]\n{chunk['document']}")
        context_block = "\n\n---\n\n".join(context_parts)
        system_content = f"{rendered_system}\n\n## Ngữ cảnh từ tài liệu:\n\n{context_block}"
    else:
        system_content = rendered_system

    messages: List[dict] = [{"role": "system", "content": system_content}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})
    return messages
