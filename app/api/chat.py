from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.session import ChatSession
from ..models.message import Message
from ..schemas.message import MessageCreate, MessageOut
from ..services import rag_service
from .. import llm_client, prompt_builder

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["chat"])


@router.get("/{session_id}/messages", response_model=List[MessageOut])
def get_messages(session_id: str, db: Session = Depends(get_db)):
    msgs = db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    ).scalars().all()
    return list(msgs)


@router.post("/{session_id}/messages")
async def send_message(session_id: str, body: MessageCreate, db: Session = Depends(get_db)):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(404, "Không tìm thấy phiên")

    doc_ids = [d.id for d in session.documents]
    doc_names = [d.original_filename for d in session.documents]

    history = db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
        .limit(session.max_history * 2)
    ).scalars().all()

    chunks = await rag_service.retrieve(body.content, doc_ids, session.top_k)

    messages = prompt_builder.build_messages(
        scenario=session.scenario,
        chunks=chunks,
        history=list(history),
        user_message=body.content,
        document_names=doc_names,
    )

    user_msg = Message(session_id=session_id, role="user", content=body.content)
    db.add(user_msg)
    db.commit()

    sources_data = [
        {
            "text": c["document"][:300] + ("..." if len(c["document"]) > 300 else ""),
            "source": c["metadata"].get("source", ""),
            "page": c["metadata"].get("page"),
        }
        for c in chunks
    ]

    async def event_stream():
        full_content = ""
        try:
            async for token in llm_client.stream_chat(
                messages,
                temperature=session.temperature,
                max_tokens=2048,
            ):
                full_content += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        except Exception as e:
            logger.exception("Streaming error")
            error_token = f"\n[Lỗi: {e}]"
            full_content += error_token
            yield f"data: {json.dumps({'type': 'token', 'content': error_token})}\n\n"

        finally:
            assistant_msg = Message(
                session_id=session_id,
                role="assistant",
                content=full_content,
                sources=json.dumps(sources_data),
            )
            db.add(assistant_msg)
            session.updated_at = datetime.utcnow()
            db.commit()

            yield f"data: {json.dumps({'type': 'done', 'sources': sources_data})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
