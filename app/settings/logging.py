from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
import logging


__all__ = ["UserActionLoggerMiddleware"]


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)


logger = logging.getLogger(__name__)


class UserActionLoggerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.text and event.text.startswith("/"):
            logger.info(f"User {event.from_user.id} issued command: {event.text}")
        elif event.text:
            logger.info(f"User {event.from_user.id} sent message: {event.text}")
        return await handler(event, data)