from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        # Храним активные соединения: {user_id: [websocket1, websocket2]}
        # Список нужен на случай, если юзер зашел и с телефона, и с компа
        self.active_connections: Dict[int, List[WebSocket]] ={}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)


    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        """Отправить сообщение конкретному пользователю во все его окна"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)

# Создаем один экземпляр на все приложение (Singleton)
manager = ConnectionManager()