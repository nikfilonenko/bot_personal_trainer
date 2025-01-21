import asyncio
from aiogram import Bot, Dispatcher

from app.handlers.v1.profile_handlers import router as router_profile_v1
from app.settings.config import config


bot = Bot(token=config.token.get_secret_value())
dp = Dispatcher()


async def main():
    dp.include_router(router_profile_v1)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())