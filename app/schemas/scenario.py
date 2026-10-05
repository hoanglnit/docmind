from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ScenarioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    tone: str = "professional"
    language: str = "vi"
    is_default: bool = False


class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    tone: Optional[str] = None
    language: Optional[str] = None
    is_default: Optional[bool] = None


class ScenarioOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    system_prompt: str
    tone: str
    language: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
