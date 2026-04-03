from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from core.exceptions import ClientDisconnectedError

logger = logging.getLogger(__name__)

DisconnectCallable = Callable[[], Awaitable[bool]]


async def check_disconnected(
    is_disconnected: DisconnectCallable | None,
) -> None:
    if is_disconnected is not None and await is_disconnected():
        logger.debug("Client disconnected — aborting cover fetch")
        raise ClientDisconnectedError("Client disconnected")
