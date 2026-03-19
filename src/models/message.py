# models/message.py

from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum  # ← переименуй, чтобы не путать
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.chat import Chat
    from src.models.user import User


class MessageStatus(str, PyEnum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chat: Mapped["Chat"] = relationship(
        "Chat",
        back_populates="messages",
        foreign_keys=[chat_id]
    )

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True
    )
    sender: Mapped["User"] = relationship("User")  # без back_populates, если не нужно

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Для медиа/файлов можно добавить отдельные поля или JSONB
    # media_type: Mapped[Optional[str]] = mapped_column(String(50))
    # media_url: Mapped[Optional[str]] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    status: Mapped[MessageStatus] = mapped_column(
        SAEnum(
            MessageStatus,
            values_callable=lambda e: [m.value for m in e],
            name="message_status",
            native_enum=True
        ),
        default=MessageStatus.SENT,
        nullable=False
    )

    # Для read receipts в группах лучше хранить отдельно (в другой таблице)
    # Но для простоты можно добавить
    read_by: Mapped[Optional[str]] = mapped_column(String(500))  # JSON список user_id или отдельная таблица
