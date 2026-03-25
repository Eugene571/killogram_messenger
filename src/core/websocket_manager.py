# src/core/websocket_manager.py

from fastapi import WebSocket
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from datetime import datetime,timezone
from src.models import User


async def _update_user_status(user_id: int, db: AsyncSession, is_online: bool):
    """Вспомогательный метод для обновления статуса в PostgreSQL"""
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(
            online_status=is_online,
            last_login=datetime.now(timezone.utc) if not is_online else User.last_login
        )
    )
    await db.execute(stmt)
    await db.commit()


class ConnectionManager:
    def __init__(self):
        # Храним активные соединения: {user_id: [websocket1, websocket2]}
        # Список нужен на случай, если юзер зашел и с телефона, и с компа
        self.active_connections: Dict[int, List[WebSocket]] ={}

    async def connect(self, user_id: int, websocket: WebSocket, db: AsyncSession):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
            await _update_user_status(user_id, db, is_online=True)
            print(f"🟢 Юзер {user_id} теперь ONLINE")

        self.active_connections[user_id].append(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket, db: AsyncSession):
        """Удаляет соединение и ставит Offline, если сокетов больше нет"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

            # Если у юзера не осталось активных вкладок/устройств
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                await _update_user_status(user_id, db, is_online=False)
                print(f"🔴 Юзер {user_id} ушел в OFFLINE")

    async def send_personal_message(self, message: dict, user_id: int):
        """Отправить сообщение конкретному пользователю во все его окна"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)

# Создаем один экземпляр на все приложение (Singleton)
manager = ConnectionManager()