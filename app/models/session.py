from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

session_documents = Table(
    "session_documents",
    Base.metadata,
    Column("session_id", String(36), ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True),
    Column("document_id", String(36), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
    Column("added_at", DateTime, default=datetime.utcnow),
)


class ChatSession(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    scenario_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("scenarios.id", ondelete="SET NULL"), nullable=True)
    top_k: Mapped[int] = mapped_column(Integer, default=5)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_history: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scenario: Mapped[Optional[Scenario]] = relationship("Scenario", lazy="select")
    documents: Mapped[List[Document]] = relationship("Document", secondary=session_documents, lazy="select")
    messages: Mapped[List[Message]] = relationship("Message", back_populates="session", cascade="all, delete-orphan", lazy="select")


from .scenario import Scenario  # noqa: E402, F401
from .document import Document  # noqa: E402, F401
from .message import Message    # noqa: E402, F401
