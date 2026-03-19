import asyncio
import sys
from logging.config import fileConfig
from os.path import dirname, abspath

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Добавляем корень проекта в sys.path, чтобы импорты из src работали
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from src.core.config import settings
from src.models.base import Base
from src.models.user import User
from src.models.chat import Chat, ChatParticipant
from src.models.message import Message

# Объект конфигурации Alembic
config = context.config

# Настройка логирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Подключаем метаданные моделей
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в 'offline' режиме."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Синхронный запуск внутри асинхронного контекста."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Запуск миграций в 'online' (асинхронном) режиме."""

    # Берем настройки из alembic.ini, но подменяем URL на тот, что в .env
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Так как Alembic внутри синхронный, используем run_sync
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Запускаем асинхронный цикл для онлайн миграций
    asyncio.run(run_migrations_online())
