import asyncio
from aiogram import Bot, Dispatcher

from app.handlers.v1.user_logic_handlers import router as router_user_logic_v1
from app.handlers.v1.activities_handlers import router as router_activities_v1
from app.settings.config import config
from app.db.db import engine, Base


bot = Bot(token=config.token_bot.get_secret_value())
dp = Dispatcher()


async def main():
    Base.metadata.create_all(bind=engine)
    dp.include_router(router_user_logic_v1)
    dp.include_router(router_activities_v1)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot was turned off.")