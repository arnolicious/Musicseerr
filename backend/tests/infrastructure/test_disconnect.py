import asyncio
import pytest
from unittest.mock import AsyncMock
from core.exceptions import ClientDisconnectedError
from infrastructure.http.disconnect import check_disconnected
from infrastructure.http.deduplication import RequestDeduplicator


@pytest.mark.anyio
async def test_check_disconnected_raises_when_disconnected():
    is_disconnected = AsyncMock(return_value=True)
    with pytest.raises(ClientDisconnectedError):
        await check_disconnected(is_disconnected)
    assert is_disconnected.await_count == 1


@pytest.mark.anyio
async def test_check_disconnected_noop_when_connected():
    is_disconnected = AsyncMock(return_value=False)
    await check_disconnected(is_disconnected)
    assert is_disconnected.await_count == 1


@pytest.mark.anyio
async def test_check_disconnected_noop_when_none():
    await check_disconnected(None)


@pytest.mark.anyio
async def test_dedup_leader_disconnect_follower_retries_as_leader():
    dedup = RequestDeduplicator()
    follower_registered = asyncio.Event()
    leader_error = None
    expected_result = ("image-bytes", "image/png", "source")

    async def leader_coro():
        await follower_registered.wait()
        raise ClientDisconnectedError("leader disconnected")

    async def run_leader():
        nonlocal leader_error
        try:
            await dedup.dedupe("key1", leader_coro)
        except ClientDisconnectedError as e:
            leader_error = e

    async def follower_coro():
        return expected_result

    async def run_follower():
        await asyncio.sleep(0)
        follower_registered.set()
        return await dedup.dedupe("key1", follower_coro)

    leader_task = asyncio.create_task(run_leader())
    await asyncio.sleep(0)
    follower_task = asyncio.create_task(run_follower())

    await asyncio.gather(leader_task, follower_task)

    assert isinstance(leader_error, ClientDisconnectedError)
    assert follower_task.result() == expected_result
