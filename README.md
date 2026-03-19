# Killogram Messenger 🚀

Асинхронный мессенджер на стеке **Python + FastAPI**. Проект сфокусирован на безопасной передаче сообщений, эффективном управлении связями между пользователями и расширяемой архитектуре чатов.

## 🛠 Стек технологий

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) — высокая производительность и встроенная поддержка асинхронности.
* **Database:** PostgreSQL + SQLAlchemy 2.0 (Async) — надежное хранилище с типизированными моделями.
* **Migrations:** Alembic — версионирование схемы БД.
* **Auth:** JWT (Access/Refresh tokens) + HttpOnly Cookies — защита сессий от XSS-атак.
* **Environment:** Poetry — современное управление зависимостями и виртуальным окружением.

## 🏗 Архитектура данных

Реализована гибкая реляционная модель для приватных и групповых коммуникаций:

* **Users:** Хеширование паролей (bcrypt), хранение `online_status` и меток последнего входа.
* **Chats:** Поддержка типов `PRIVATE` и `GROUP`. Оптимизировано через `last_message_id` для быстрого рендеринга списка чатов.
* **Messages:** Текстовый контент, статусы (`SENT`, `DELIVERED`, `READ`) и каскадное управление жизненным циклом.
* **Participants:** Промежуточная таблица Many-to-Many с метаданными: роли (admin), время вступления и `last_read_message_id`.

## 🚀 Быстрый старт

### 1. Подготовка окружения
Убедитесь, что у вас установлен **Poetry**.

```bash
git clone [https://github.com/YourUsername/killogram.git](https://github.com/YourUsername/killogram.git)
cd killogram
poetry install
```
### 2. Конфигурация
Создайте файл .env в корне проекта (см. .env.example):

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/killogram
SECRET_KEY=your_generate_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```
### 3. Применение миграций
```Bash
poetry run alembic upgrade head
```
### 4. Запуск сервера
```Bash
poetry run uvicorn main:app --reload
```
После запуска интерактивная документация (Swagger) доступна по адресу: http://127.0.0.1:8000/docs

## 🔒 Безопасность
> Password Security: Использование passlib с библиотекой bcrypt исключает хранение паролей в открытом виде.

> Secure Cookies: Токены авторизации передаются через HttpOnly куки, что предотвращает их кражу через вредоносные JS-скрипты.

> Access Control: Защита эндпоинтов реализована через Dependency Injection (Depends), гарантируя доступ к данным только владельцам сессий.

📈 Roadmap (В разработке)
[x] Система аутентификации и JWT-авторизация.

[x] Профили пользователей и эндпоинт /me.

[ ] Логика создания приватных чатов (проверка дубликатов).

[ ] WebSocket интеграция для мгновенного обмена сообщениями.

[ ] Поддержка групповых чатов и управление участниками.