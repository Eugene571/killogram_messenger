from datetime import datetime

from sqlalchemy import String, Boolean, DateTime
from typing import Optional, List

from src.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    username: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    online_status: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    chats: Mapped[List["Chat"]] = relationship(
        "Chat",
        secondary="chat_participants",
        back_populates="participants"
    )
    chat_participations: Mapped[List["ChatParticipant"]] = relationship(
        "ChatParticipant",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    created_chats: Mapped[List["Chat"]] = relationship(
        "Chat",
        back_populates="creator",
        foreign_keys="[Chat.creator_id]"
    )