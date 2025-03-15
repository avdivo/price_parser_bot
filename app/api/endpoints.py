import asyncio

from aiogram.types import Update
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Config
from app.core.database import get_db
from app.core.config_bot import bot, dp

webhook_router = APIRouter()


@webhook_router.post(Config.WEBHOOK_PATH, include_in_schema=False)
async def handle_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Обработка запросов. Передача боту.
    """
    update_data = await request.json()  # Получение данных из запроса
    update = Update(**update_data)  # Создание объекта обновления
    asyncio.create_task(dp.feed_update(bot, update, db=db))  # Передача обновления боту
    return JSONResponse(content={})  # Возвращение пустого ответа


@webhook_router.get("/")
def read_root():
    return {"message": "Welcome to ProductWBsyncBot!"}
