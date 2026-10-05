from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    name: str
    original_filename: str
    content_type: str
    file_size: int
    chunk_count: int
    status: str
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
