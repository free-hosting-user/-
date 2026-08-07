import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from handlers import admin, moderation

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(admin.router)
    dp.include_router(moderation.router)

    logging.info("Starting Telegram Moderation Bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
