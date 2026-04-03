import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.genre_cover_prewarm_service import (
    GenreCoverPrewarmService,
    _PREWARM_INTER_ITEM_DELAY,
)


def _make_cover_repo() -> MagicMock:
    repo = MagicMock()
    repo.get_artist_image = AsyncMock(return_value=(b"img", "image/jpeg", "audiodb"))
    repo.get_release_group_cover = AsyncMock(return_value=(b"img", "image/jpeg", "audiodb"))
    return repo


@pytest.mark.asyncio
async def test_schedule_prewarm_calls_cover_repo_for_artists_and_albums():
    repo = _make_cover_repo()
    svc = GenreCoverPrewarmService(cover_repo=repo)

    svc.schedule_prewarm("rock", ["a1", "a2"], ["b1"])
    await asyncio.sleep(0.1)
    task = svc._active_genres.get("rock")
    if task:
        await task

    assert repo.get_artist_image.await_count == 2
    assert repo.get_release_group_cover.await_count == 1


@pytest.mark.asyncio
async def test_schedule_prewarm_deduplicates_same_genre():
    repo = _make_cover_repo()

    async def _slow_fetch(*args, **kwargs):
        await asyncio.sleep(0.5)
        return (b"img", "image/jpeg", "audiodb")

    repo.get_artist_image = AsyncMock(side_effect=_slow_fetch)
    svc = GenreCoverPrewarmService(cover_repo=repo)

    svc.schedule_prewarm("rock", ["a1"], [])
    svc.schedule_prewarm("rock", ["a2", "a3"], [])
    await asyncio.sleep(0.05)

    assert len(svc._active_genres) == 1
    task = svc._active_genres["rock"]
    await task

    assert repo.get_artist_image.await_count == 1


@pytest.mark.asyncio
async def test_error_isolation_per_item():
    repo = _make_cover_repo()
    call_count = 0

    async def _artist_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("boom")
        return (b"img", "image/jpeg", "audiodb")

    repo.get_artist_image = AsyncMock(side_effect=_artist_side_effect)
    svc = GenreCoverPrewarmService(cover_repo=repo)

    svc.schedule_prewarm("jazz", ["fail", "ok"], [])
    await asyncio.sleep(0.1)
    task = svc._active_genres.get("jazz")
    if task:
        await task

    assert repo.get_artist_image.await_count == 2


@pytest.mark.asyncio
async def test_done_callback_does_not_remove_new_task():
    repo = _make_cover_repo()
    svc = GenreCoverPrewarmService(cover_repo=repo)

    blocker = asyncio.Event()
    original_prewarm = svc._prewarm

    async def _slow_prewarm(*args, **kwargs):
        await blocker.wait()

    svc._prewarm = _slow_prewarm
    svc.schedule_prewarm("pop", ["a1"], [])
    first_task = svc._active_genres["pop"]

    blocker.set()
    await first_task

    svc._prewarm = original_prewarm
    svc.schedule_prewarm("pop", ["a2"], [])
    second_task = svc._active_genres.get("pop")

    assert second_task is not None
    assert second_task is not first_task
    await second_task


@pytest.mark.asyncio
async def test_shutdown_cancels_active_tasks():
    repo = _make_cover_repo()
    repo.get_artist_image = AsyncMock(side_effect=lambda *a, **kw: asyncio.sleep(10))
    svc = GenreCoverPrewarmService(cover_repo=repo)

    svc.schedule_prewarm("metal", [f"m{i}" for i in range(5)], [])
    await asyncio.sleep(0.1)

    assert len(svc._active_genres) == 1
    await svc.shutdown()
    assert len(svc._active_genres) == 0


@pytest.mark.asyncio
async def test_shutdown_is_idempotent_when_no_tasks():
    repo = _make_cover_repo()
    svc = GenreCoverPrewarmService(cover_repo=repo)
    await svc.shutdown()
    assert len(svc._active_genres) == 0


@pytest.mark.asyncio
async def test_cleanup_after_task_completes():
    repo = _make_cover_repo()
    svc = GenreCoverPrewarmService(cover_repo=repo)

    svc.schedule_prewarm("blues", ["a1"], [])
    task = svc._active_genres["blues"]
    await task
    await asyncio.sleep(0.05)

    assert "blues" not in svc._active_genres
