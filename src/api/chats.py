# src/api/chats.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.security import get_current_active_user
from src.models import User
from src.schemas.chat import ChatOut
from src.services.chat import ChatService
from src.schemas.message import MessageCreate

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
