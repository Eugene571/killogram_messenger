# src/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """"Общие поля как для создания, так и для вывода юзера"""
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Имя пользователя (уникальное)"
    )
    email: EmailStr = Field(
        ...,
        description="Адрес эл. почты"
    )


class UserCreate(UserBase):
    """Схема для регистрации"""
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Пароль"  #  захешировать
    )


class UserOut(UserBase):
    """Схема для ответа клиенту без пароля"""
    id: int
    online_status: bool = False
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
    # json_encoders = {datetime: lambda v: v.isoformat()}
