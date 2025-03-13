import logging
from fastapi import FastAPI

from app.api.endpoints import webhook_router
from app.core.config import Config
from app.core.database import create_tables
from app.core.config_bot import bot, dp

app = FastAPI(title="Парсер цен товаров с ботом")
app.include_router(webhook_router)  # Подключение маршрутов

logging.basicConfig(level=logging.INFO)  # Лог файл не создается, логи выводятся в консоль


# События
@app.on_event("startup")
async def on_startup():
    """Установка вебхука телеграмм, создание таблиц"""

    # Установка вебхука
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != Config.WEBHOOK_URL:
        await bot.set_webhook(Config.WEBHOOK_URL)
    logging.info(f"Webhook set to URL: {Config.WEBHOOK_URL}")

    # Создание таблиц в БД
    await create_tables()


@app.on_event("shutdown")
async def on_shutdown():
    """Удаление вебхука и закрытие хранилища при завершении работы приложения"""
    await bot.delete_webhook()
    await dp.storage.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",  # Путь к приложению
        host="0.0.0.0",  # Хост
        port=int(Config.APP_PORTS),  # Порт
        reload=True  # Для автоперезагрузки при изменениях в коде
    )
