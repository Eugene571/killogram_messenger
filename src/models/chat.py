from datetime import datetime
from enum import Enum as PyEnum          # ← переименуй, чтобы не путать
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from typing import Optional, List

from src.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.user import User


class ChatType(str, PyEnum):
    PRIVATE = "private"
    GROUP = "group"


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    type: Mapped[ChatType] = mapped_column(
        SAEnum(
            ChatType,
            values_callable=lambda e: [m.value for m in e],  # ← e — это ChatType (класс)
            name="chat_type",  # ← обязательно для PostgreSQL native enum
            native_enum=True,  # ← по умолчанию True в PostgreSQL
        ),
        nullable=False,
        index=True
    )

    name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    creator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[creator_id],
        back_populates="created_chats"
    )

    participants: Mapped[List["User"]] = relationship(
        "User",
        secondary="chat_participants",
        passive_deletes=True
    )

    last_message_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    last_message: Mapped[Optional["Message"]] = relationship(
        "Message",
        foreign_keys=[last_message_id],
        uselist=False,
        remote_side="Message.id"
    )

    # Для private чатов — кэш собеседника (можно вычислять динамически, но иногда хранят для скорости)
    # Вариант: не хранить, а вычислять при запросе

    # Дополнительно: можно добавить поля is_pinned, is_muted и т.д. для каждого пользователя

    # Связи для обратной стороны (если нужно)
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


# Промежуточная таблица many-to-many: User ↔ Chat
class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"),
        primary_key=True
    )

    # Дополнительные поля на связь (очень полезно!)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    last_read_message_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True
    )
    # muted_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="chat_participations")
    chat: Mapped["Chat"] = relationship("Chat", back_populates="participants")