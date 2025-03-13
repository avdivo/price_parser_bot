from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import Config
from app.bot.handlers import register_handlers

bot = Bot(token=Config.BOT_TOKEN)
router = Router()
register_handlers(router)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_router(router)
