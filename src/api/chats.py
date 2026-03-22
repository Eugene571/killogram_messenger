# src/api/chats.py

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.security import get_current_active_user
from src.models import User
from src.schemas.chat import ChatOut
from src.services.chat import ChatService
from src.schemas.message import MessageCreate
from src.core.websocket_manager import manager
from src.core.redis import redis_client
import asyncio
import json

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/direct/{recipient_id}")
async def create_direct_chat(
        recipient_id: int,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    # Нельзя создать чат с самим собой (хотя в Telegram можно, но у нас пока нет)
    if recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot chat with yourself yet")

    service = ChatService(db)
    chat = await service.get_or_create_private_chat(current_user.id, recipient_id)
    return {"chat_id": chat.id, "type": chat.type}


@router.get("/", response_model=list[ChatOut])
async def get_my_chats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = ChatService(db)
    chats = await service.get_user_chats(current_user.id)

    output = []
    for chat in chats:
        # 1. Логика определения имени чата
        # Если это приватный чат и имя не задано — берем имя собеседника
        display_name = chat.name
        if chat.type == "private" and not display_name:
            # Ищем в подгруженных участниках того, кто НЕ текущий юзер
            other = next((p for p in chat.participants if p.id != current_user.id), None)
            if other:
                display_name = other.username

        # 2. Формируем словарь данных (DTO)
        # Наполняем его всеми полями, которые требует схема ChatOut
        chat_data = {
            "id": chat.id,
            "type": chat.type,
            "name": display_name,
            "description": chat.description,
            "created_at": chat.created_at,
            "creator_id": chat.creator_id,
            "participant_count": len(chat.participants),
            "last_message_content": chat.last_message.content if chat.last_message else None,
            "last_message_at": chat.last_message.created_at if chat.last_message else None,
        }

        # 3. Валидируем через Pydantic и добавляем в итоговый список
        output.append(ChatOut(**chat_data))

    return output

@router.post("/{chat_id}/messages")
async def send_chat_message(
        chat_id: int,
        data: MessageCreate,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    service = ChatService(db)
    message = await service.send_message(
        chat_id=chat_id,
        sender_id=current_user.id,
        content=data.content
    )
    return {"status": "ok", "message_id": message.id}


async def redis_listener(websocket: WebSocket, chat_id: int):
    """Вспомогательная функция: слушает Redis и пушит в WebSocket"""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"chat_{chat_id}")

    # Маленький лайфхак: проверяем, что подписка активна
    print(f"📡 Subscribed to chat_{chat_id}")

    try:
        while True:
            # Используем get_message вместо listen() для более стабильной работы в цикле
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is not None:
                print(f"📩 Got from Redis: {message['data']}")
                await websocket.send_text(message["data"])

            # Даем asyncio передохнуть
            await asyncio.sleep(0.01)

    except asyncio.CancelledError:
        await pubsub.unsubscribe()
        print(f"🔌 Unsubscribed from chat_{chat_id}")
    except Exception as e:
        print(f"🔴 Redis listener error: {e}")
    finally:
        await pubsub.unsubscribe()


@router.websocket("/ws/{chat_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int, user_id: int):
    # 1. Регистрация соединения в нашем менеджере
    await manager.connect(user_id, websocket)

    # 2. Запуск фонового слушателя Redis
    # Теперь этот сокет «подписан» на обновления конкретного чата
    listener_task = asyncio.create_task(redis_listener(websocket, chat_id))

    try:
        while True:
            # Ждем данных от клиента. Если клиент ничего не шлет,
            # мы просто висим тут, пока сокет не закроется.
            await websocket.receive_text()
    except WebSocketDisconnect:
        # 3. Юзер ушел — отменяем подписку на Redis и удаляем из менеджера
        listener_task.cancel()
        manager.disconnect(user_id, websocket)