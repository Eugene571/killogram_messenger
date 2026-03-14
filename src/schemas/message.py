# src/schemas/message.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum as PyEnum


class MessageStatus(str, PyEnum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class MessageCreate(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=8192,
        description="Текст сообщения"
    )
    # chat_id передаётся в пути или заголовке, не в теле


class MessageOut(BaseModel):
    """Возвращается клиенту(websocket/http)"""
    id: int
    chat_id: int
    sender_id: int
    sender_username: Optional[str] = None
    content: str
    created_at: datetime
    status: MessageStatus
    read_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

