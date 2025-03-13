import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

# Импортируем конфигурацию
from .config import Config

# URL для подключения к базе данных SQLite
DATABASE_URL = f"sqlite+aiosqlite:///{Config.DB_NAME}"

# Создание асинхронного движка SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False)  # Логи выключены

# Создание асинхронной фабрики сессий
async_session = async_sessionmaker(engine, expire_on_commit=False)


# Базовый класс для моделей
class Base(AsyncAttrs, DeclarativeBase):
    pass


# Создаем все таблицы, определенные в моделях
async def create_tables():
    from app.models.models import ProductInfo, PriceScan
    print('Создание ДЮ')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Функция для получения асинхронной сессии
async def get_db():
    async with async_session() as session:
        yield session
