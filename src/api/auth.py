#src/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from src.core.database import get_db
from src.models import User
from src.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    SECRET_KEY, ALGORITHM, get_current_active_user
)
from src.schemas.user import UserCreate, UserOut
from jose import jwt, JWTError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Проверка уникальности (username или email)
    query = select(User).where(
        or_(User.username == user_in.username, User.email == user_in.email)
    )
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем или email уже существует"
        )

    # 2. Создание записи
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login")
async def login(
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    # 1. Поиск пользователя
    query = select(User).where(User.username == form_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    # 2. Проверка существования и пароля
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Генерируем токены
    access_token = create_access_token(data={"sub": form_data.username})
    refresh_token = create_refresh_token(data={"sub": form_data.username})

    # 4. Установка Cookies
    cookie_params = {
        "httponly": True,
        "samesite": "lax",
        "secure": False,  # Для разработки на localhost
    }

    response.set_cookie(key="access_token", value=access_token, max_age=15 * 60, **cookie_params)
    response.set_cookie(key="refresh_token", value=refresh_token, max_age=7 * 24 * 3600, **cookie_params)

    return {"message": "Logged in successfully", "username": user.username}


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        username = payload.get("sub")
        # создаем новый access
        new_access = create_access_token(data={"sub": username})

        response.set_cookie(
            key="access_token",
            value=new_access,
            httponly=True,
            max_age=15 * 60,
            samesite="lax"
        )
        return {"message": "Token refreshed"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Возвращает профиль текущего пользователя.
    Работает только если есть валидная кука 'access_token'.
    """
    return current_user
