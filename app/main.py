import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import Config
from app.core.config_bot import bot, dp
from app.core.database import create_tables
from app.api.endpoints import webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Код для startup и shutdown
    """
    # startup
    # Установка вебхука
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != Config.WEBHOOK_URL:
        await bot.set_webhook(Config.WEBHOOK_URL)
    logging.info(f"Webhook set to URL: {Config.WEBHOOK_URL}")
    # Создание таблиц в БД
    await create_tables()

    yield

    # shutdown
    await bot.delete_webhook()  # Удаление вебхука
    await dp.storage.close()  # Закрытие хранилища


app = FastAPI(lifespan=lifespan, title="Парсер цен товаров с ботом")  # FastAPI сам вызовет lifespan()
app.include_router(webhook_router)  # Подключение маршрутов

logging.basicConfig(level=logging.INFO)  # Лог файл не создается, логи выводятся в консоль

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",  # Путь к приложению
        host="0.0.0.0",  # Хост
        port=int(Config.APP_PORTS),  # Порт
        reload=True  # Для автоперезагрузки при изменениях в коде
    )
