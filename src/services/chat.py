# src/services/chat.py

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from src.models.chat import Chat, ChatParticipant, ChatType
from src.models.user import User


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_private_chat(self, user_id_1: int, user_id_2: int) -> Chat:
        # 1. Ищем, существует ли уже приватный чат между этими двумя.
        # Используем подзапрос для поиска чата, где есть оба ID
        stmt = (
            select(Chat)
            .join(ChatParticipant)
            .where(
                and_(
                    Chat.type == ChatType.PRIVATE,
                    ChatParticipant.user_id.in_([user_id_1, user_id_2])
                )
            )
            .group_by(Chat.id)
            # Если нашли чат, где количество участников из нашего списка = 2
            .having(func.count(ChatParticipant.user_id) == 2)
        )
        result = await self.db.execute(stmt)
        existing_chat = result.scalar_one_or_none()

        if existing_chat:
            return existing_chat

        # 2. Если чата нет — создаем новый
        new_chat = Chat(type=ChatType.PRIVATE)
        self.db.add(new_chat)
        await self.db.flush()  # Получаем ID чата без коммита всей транзакции

        # 3. Добавляем обоих участников
        participants = [
            ChatParticipant(user_id=user_id_1, chat_id=new_chat.id),
            ChatParticipant(user_id=user_id_2, chat_id=new_chat.id)
        ]
        self.db.add_all(participants)

        await self.db.commit()
        await self.db.refresh(new_chat)
        return new_chat

    async def get_user_chats(self, user_id: int):
        # Запрос: найти все чаты текущего пользователя
        # Сразу загружаем участников и последнее сообщение
        stmt = (
            select(Chat)
            .join(ChatParticipant)
            .where(ChatParticipant.user_id == user_id)
            .options(
                joinedload(Chat.participants),
                joinedload(Chat.last_message)
            )
            .order_by(Chat.created_at.desc())
        )

        result = await self.db.execute(stmt)
        return result.unique().scalars().all()
