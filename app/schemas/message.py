from __future__ import annotations
import json
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, model_validator


class MessageCreate(BaseModel):
    content: str


class SourceRef(BaseModel):
    text: str
    source: str
    page: Optional[int] = None


class MessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: List[SourceRef] = []
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_sources(cls, data):
        if hasattr(data, "__dict__"):
            raw = getattr(data, "sources", None)
            if isinstance(raw, str):
                try:
                    data.__dict__["sources"] = json.loads(raw)
                except Exception:
                    data.__dict__["sources"] = []
        return data
