# src/api/chats.py

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.database import get_db
from src.core.security import get_current_active_user
from src.models import User, ChatParticipant
from src.schemas.chat import ChatOut
from src.services.chat import ChatService
from src.schemas.message import MessageCreate
from src.core.websocket_manager import manager
from src.core.redis import redis_client
from src.core.security import get_current_active_user, get_current_user, oauth2_scheme
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


@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
        websocket: WebSocket,
        chat_id: int,
        token: str = Query(None),  # Добавляем поддержку ?token=...
        db: AsyncSession = Depends(get_db)
):

    # 1. Берем токен из Query-параметра или из кук (на всякий случай)
    auth_token = token or websocket.cookies.get("access_token")

    if not auth_token:
        print("🔴 Токен не найден ни в URL, ни в куках")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        # Используем твою логику проверки
        user = await get_current_active_user(
            token_data=await get_current_user(token=auth_token),
            db=db
        )
    except Exception as e:
        print(f"🔴 Ошибка валидации: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 2. Проверка участия в чате (оставляем как было)
    stmt = select(ChatParticipant).where(
        ChatParticipant.chat_id == chat_id,
        ChatParticipant.user_id == user.id
    )
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        print(f"🚫 Юзер {user.username} не в чате {chat_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 3. Подключение
    await manager.connect(user.id, websocket)
    listener_task = asyncio.create_task(redis_listener(websocket, chat_id))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        listener_task.cancel()
        manager.disconnect(user.id, websocket)