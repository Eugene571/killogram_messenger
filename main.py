# main.py
# import src.models
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.auth import router as auth_router
from src.api.chats import router as chat_router

app = FastAPI(
    title="Killogram Messenger API",
    version="0.1.0"
)
# Настройка CORS (чтобы фронтенд мог достучаться до бэкенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
