import asyncio
import logging
from unittest.mock import AsyncMock, patch

import pytest

from core.tasks import cleanup_cache_periodically, sync_request_statuses_periodically


@pytest.mark.asyncio
async def test_cleanup_cache_logs_errors_at_error_level(caplog):
    cache = AsyncMock()
    cache.cleanup_expired.side_effect = RuntimeError("cache boom")

    caplog.set_level(logging.ERROR, logger="core.tasks")

    async def fake_sleep(_: int) -> None:
        if cache.cleanup_expired.await_count:
            raise asyncio.CancelledError()

    with patch("core.tasks.asyncio.sleep", side_effect=fake_sleep):
        await cleanup_cache_periodically(cache, interval=1)

    assert any(
        record.levelno == logging.ERROR
        and record.name == "core.tasks"
        and "Cache cleanup task failed" in record.message
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_request_status_sync_logs_errors_at_error_level(caplog):
    requests_page_service = AsyncMock()
    requests_page_service.sync_request_statuses.side_effect = RuntimeError("sync boom")

    caplog.set_level(logging.ERROR, logger="core.tasks")

    async def fake_sleep(_: int) -> None:
        if requests_page_service.sync_request_statuses.await_count:
            raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        with patch("core.tasks.asyncio.sleep", side_effect=fake_sleep):
            await sync_request_statuses_periodically(requests_page_service, interval=1)

    assert any(
        record.levelno == logging.ERROR
        and record.name == "core.tasks"
        and "Periodic request status sync failed" in record.message
        for record in caplog.records
    )
