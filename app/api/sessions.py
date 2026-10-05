from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.session import ChatSession
from ..models.document import Document
from ..models.message import Message
from ..schemas.session import SessionCreate, SessionUpdate, SessionDocumentsUpdate, SessionOut

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _to_out(session: ChatSession, db: Session) -> SessionOut:
    count = db.execute(
        select(func.count()).where(Message.session_id == session.id)
    ).scalar_one()
    data = SessionOut.model_validate(session)
    data.message_count = count
    return data


@router.get("", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
    return [_to_out(s, db) for s in sessions]


@router.post("", response_model=SessionOut, status_code=201)
def create_session(body: SessionCreate, db: Session = Depends(get_db)):
    session = ChatSession(
        name=body.name,
        scenario_id=body.scenario_id,
        top_k=body.top_k,
        temperature=body.temperature,
        max_history=body.max_history,
    )
    if body.document_ids:
        docs = db.execute(
            select(Document).where(Document.id.in_(body.document_ids), Document.status == "ready")
        ).scalars().all()
        session.documents = list(docs)

    db.add(session)
    db.commit()
    db.refresh(session)
    return _to_out(session, db)


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: str, db: Session = Depends(get_db)):
    s = db.get(ChatSession, session_id)
    if not s:
        raise HTTPException(404, "Không tìm thấy phiên")
    return _to_out(s, db)


@router.patch("/{session_id}", response_model=SessionOut)
def update_session(session_id: str, body: SessionUpdate, db: Session = Depends(get_db)):
    s = db.get(ChatSession, session_id)
    if not s:
        raise HTTPException(404, "Không tìm thấy phiên")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return _to_out(s, db)


@router.patch("/{session_id}/documents", response_model=SessionOut)
def update_session_documents(session_id: str, body: SessionDocumentsUpdate, db: Session = Depends(get_db)):
    s = db.get(ChatSession, session_id)
    if not s:
        raise HTTPException(404, "Không tìm thấy phiên")

    if body.add_ids:
        to_add = db.execute(
            select(Document).where(Document.id.in_(body.add_ids), Document.status == "ready")
        ).scalars().all()
        existing_ids = {d.id for d in s.documents}
        for doc in to_add:
            if doc.id not in existing_ids:
                s.documents.append(doc)

    if body.remove_ids:
        s.documents = [d for d in s.documents if d.id not in body.remove_ids]

    db.commit()
    db.refresh(s)
    return _to_out(s, db)


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: str, db: Session = Depends(get_db)):
    s = db.get(ChatSession, session_id)
    if not s:
        raise HTTPException(404, "Không tìm thấy phiên")
    db.delete(s)
    db.commit()
