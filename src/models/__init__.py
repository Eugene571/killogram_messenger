# src/models/__init__.py

from src.models.base import Base
from src.models.user import User
from src.models.chat import Chat, ChatParticipant  # Импортируй все свои модели чатов
from src.models.message import Message            # И сообщений

# Теперь все эти классы зарегистрированы в Base.metadata
__all__ = [
    "Base",
    "User",
    "Chat",
    "ChatParticipant",
    "Message",
]
