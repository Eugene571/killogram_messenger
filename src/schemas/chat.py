# src/schemas/chat.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum as PyEnum


class ChatType(str, PyEnum):
    PRIVATE = "private"
    GROUP = "group"


class ChatBase(BaseModel):
    type: ChatType
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class ChatCreate(ChatBase):
    """
    При создании чата:
    - для private: type=private + participant_ids (второй пользователь)
    - для group: type=group + name + опционально description + participant_ids
    """
    participant_ids: List[int] = Field(
        ...,
        min_length=1,
        description="ID пользователей, которых добавить в чат (для private — ровно один)"
    )


class ChatOut(ChatBase):
    id: int
    created_at: datetime
    creator_id: Optional[int] = None

    last_message_content: Optional[str] = None
    last_message_at: Optional[datetime] = None
    participant_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
