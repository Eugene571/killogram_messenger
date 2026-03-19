# src/api/dependencies.py

# from fastapi import Depends, HTTPException, status, Cookie
# from jose import JWTError, jwt
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from src.core.database import get_db
# from src.models.user import User
# from src.schemas.token import TokenData
# from src.core.config import settings  # Здесь должен быть SECRET_KEY и ALGORITHM
#
#
# async def get_current_user(
#         # FastAPI сам достанет значение из куки с именем access_token
#         access_token: str | None = Cookie(None),
#         db: AsyncSession = Depends(get_db)
# ) -> User:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#
#     if not access_token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Not authenticated"
#         )
#
#     try:
#         # Декодируем токен
#         payload = jwt.decode(
#             access_token,
#             settings.SECRET_KEY,
#             algorithms=[settings.ALGORITHM]
#         )
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except JWTError:
#         raise credentials_exception
#
#     # Ищем пользователя в БД по username (или id, если в sub положил id)
#     query = select(User).where(User.username == token_data.username)
#     result = await db.execute(query)
#     user = result.scalar_one_or_none()
#
#     if user is None:
#         raise credentials_exception
#
#     return user

