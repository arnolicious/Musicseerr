import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.tasks import cleanup_disk_cache_periodically


@pytest.mark.asyncio
async def test_periodic_cleanup_calls_both_caches():
    disk_cache = AsyncMock()
    cover_disk_cache = AsyncMock()

    iteration_count = 0

    original_cleanup = cleanup_disk_cache_periodically

    async def run_one_iteration():
        nonlocal iteration_count
        task = asyncio.create_task(
            original_cleanup(disk_cache, interval=0, cover_disk_cache=cover_disk_cache)
        )
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    await run_one_iteration()

    disk_cache.cleanup_expired_recent.assert_called()
    disk_cache.enforce_recent_size_limits.assert_called()
    disk_cache.cleanup_expired_covers.assert_called()
    disk_cache.enforce_cover_size_limits.assert_called()
    cover_disk_cache.enforce_size_limit.assert_called_with(force=True)


@pytest.mark.asyncio
async def test_periodic_cleanup_works_without_cover_cache():
    disk_cache = AsyncMock()

    task = asyncio.create_task(
        cleanup_disk_cache_periodically(disk_cache, interval=0, cover_disk_cache=None)
    )
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    disk_cache.cleanup_expired_recent.assert_called()
    disk_cache.enforce_recent_size_limits.assert_called()
    disk_cache.cleanup_expired_covers.assert_called()
    disk_cache.enforce_cover_size_limits.assert_called()


@pytest.mark.asyncio
async def test_periodic_cleanup_continues_on_cover_cache_error():
    disk_cache = AsyncMock()
    cover_disk_cache = AsyncMock()
    cover_disk_cache.enforce_size_limit.side_effect = [RuntimeError("disk full"), None]

    task = asyncio.create_task(
        cleanup_disk_cache_periodically(disk_cache, interval=0, cover_disk_cache=cover_disk_cache)
    )
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert cover_disk_cache.enforce_size_limit.call_count >= 1
    assert disk_cache.cleanup_expired_recent.call_count >= 1
