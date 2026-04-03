import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock

from services.home.genre_service import GenreService


def _make_service() -> tuple[GenreService, AsyncMock]:
    mb = AsyncMock()
    mem_cache = AsyncMock()
    mem_cache.get = AsyncMock(return_value=None)
    mem_cache.set = AsyncMock()
    svc = GenreService(
        musicbrainz_repo=mb,
        memory_cache=mem_cache,
    )
    return svc, mb


def _make_artist(mbid: str) -> MagicMock:
    a = MagicMock()
    a.musicbrainz_id = mbid
    return a


class TestGenreBatchParallel:
    @pytest.mark.asyncio
    async def test_genre_batch_fires_parallel(self):
        """All genre lookups should start before any finishes (parallel execution)."""
        svc, mb = _make_service()
        start_times: list[float] = []
        end_times: list[float] = []
        loop = asyncio.get_event_loop()

        original_search = mb.search_artists_by_tag

        async def tracking_search(genre_name, limit=10):
            start_times.append(loop.time())
            await asyncio.sleep(0.05)
            end_times.append(loop.time())
            return [_make_artist(f"mbid-{genre_name}")]

        mb.search_artists_by_tag = tracking_search

        genres = ["rock", "pop", "jazz", "metal", "blues"]
        results = await svc.get_genre_artists_batch(genres)

        assert len(results) == 5
        # All starts should be before the first end (proves parallelism)
        assert max(start_times) < min(end_times)

    @pytest.mark.asyncio
    async def test_genre_batch_deduplicates(self):
        """When two genres resolve the same MBID, the second gets re-resolved."""
        svc, mb = _make_service()
        shared_mbid = "shared-aaaa-bbbb-cccc-dddddddddddd"
        alt_mbid = "alt-eeee-ffff-gggg-hhhhhhhhhhhh"
        call_count = 0

        async def search_returning_same(genre_name, limit=10):
            nonlocal call_count
            call_count += 1
            if call_count > 2 and genre_name == "pop":
                return [_make_artist(alt_mbid)]
            return [_make_artist(shared_mbid)]

        mb.search_artists_by_tag = search_returning_same

        genres = ["rock", "pop"]
        results = await svc.get_genre_artists_batch(genres)

        # rock gets the shared mbid, pop should be re-resolved
        assert results["rock"] == shared_mbid
        assert results["pop"] == alt_mbid

    @pytest.mark.asyncio
    async def test_genre_batch_empty_input(self):
        """Empty genre list returns empty dict."""
        svc, _ = _make_service()
        result = await svc.get_genre_artists_batch([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_genre_batch_handles_none_results(self):
        """Genres with no matching artist return None."""
        svc, mb = _make_service()

        async def no_results(genre_name, limit=10):
            return []

        mb.search_artists_by_tag = no_results

        genres = ["nonexistent"]
        results = await svc.get_genre_artists_batch(genres)
        assert results == {"nonexistent": None}

    @pytest.mark.asyncio
    async def test_genre_batch_caps_at_20(self):
        """Only processes the first 20 genres."""
        svc, mb = _make_service()

        async def simple_search(genre_name, limit=10):
            return [_make_artist(f"mbid-{genre_name}")]

        mb.search_artists_by_tag = simple_search

        genres = [f"genre-{i}" for i in range(25)]
        results = await svc.get_genre_artists_batch(genres)
        assert len(results) == 20
