from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from .document import DocumentOut
from .scenario import ScenarioOut


class SessionCreate(BaseModel):
    name: str
    scenario_id: Optional[str] = None
    document_ids: List[str] = []
    top_k: int = 5
    temperature: float = 0.7
    max_history: int = 10


class SessionUpdate(BaseModel):
    name: Optional[str] = None
    scenario_id: Optional[str] = None
    top_k: Optional[int] = None
    temperature: Optional[float] = None
    max_history: Optional[int] = None


class SessionDocumentsUpdate(BaseModel):
    add_ids: List[str] = []
    remove_ids: List[str] = []


class SessionOut(BaseModel):
    id: str
    name: str
    scenario_id: Optional[str]
    top_k: int
    temperature: float
    max_history: int
    created_at: datetime
    updated_at: datetime
    documents: List[DocumentOut] = []
    scenario: Optional[ScenarioOut] = None
    message_count: int = 0

    model_config = {"from_attributes": True}
