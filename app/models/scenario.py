from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

DEFAULT_SYSTEM_PROMPT = """Bạn là trợ lý AI thông minh, chuyên hỗ trợ tra cứu và phân tích tài liệu.

{% if documents %}Bạn có quyền truy cập vào các tài liệu:
{% for doc in documents %}- {{ doc }}
{% endfor %}{% endif %}

Khi trả lời hãy:
1. Dựa vào ngữ cảnh tài liệu được cung cấp
2. Trích dẫn nguồn cụ thể (tên file, trang) khi có thể
3. Thành thật nếu không tìm thấy thông tin trong tài liệu
4. Trả lời bằng ngôn ngữ người dùng đang dùng"""


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, default=DEFAULT_SYSTEM_PROMPT)
    tone: Mapped[str] = mapped_column(String(50), default="professional")
    language: Mapped[str] = mapped_column(String(10), default="vi")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
