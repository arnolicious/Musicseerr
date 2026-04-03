import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from core.exceptions import ClientDisconnectedError
from infrastructure.queue.priority_queue import RequestPriority
from repositories.coverart_artist import ArtistImageFetcher
from repositories.coverart_album import AlbumCoverFetcher


@pytest.mark.anyio
async def test_artist_fetcher_bails_before_audiodb():
    fetcher = ArtistImageFetcher(
        http_get_fn=AsyncMock(),
        write_cache_fn=AsyncMock(),
        cache=MagicMock(),
    )
    fetcher._fetch_from_audiodb = AsyncMock()

    is_disconnected = AsyncMock(return_value=True)
    with pytest.raises(ClientDisconnectedError):
        await fetcher.fetch_artist_image(
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            None,
            Path("/tmp/test"),
            is_disconnected=is_disconnected,
        )
    fetcher._fetch_from_audiodb.assert_not_awaited()


@pytest.mark.anyio
async def test_artist_fetcher_bails_between_audiodb_and_local():
    fetcher = ArtistImageFetcher(
        http_get_fn=AsyncMock(),
        write_cache_fn=AsyncMock(),
        cache=MagicMock(),
    )
    fetcher._fetch_from_audiodb = AsyncMock(return_value=None)
    fetcher._fetch_local_sources = AsyncMock(return_value=(None, False))

    call_count = 0

    async def disconnect_after_first():
        nonlocal call_count
        call_count += 1
        return call_count > 1

    with pytest.raises(ClientDisconnectedError):
        await fetcher.fetch_artist_image(
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            None,
            Path("/tmp/test"),
            is_disconnected=disconnect_after_first,
        )
    fetcher._fetch_from_audiodb.assert_awaited_once()
    fetcher._fetch_local_sources.assert_not_awaited()


@pytest.mark.anyio
async def test_album_fetcher_bails_before_caa():
    fetcher = AlbumCoverFetcher(
        http_get_fn=AsyncMock(),
        write_cache_fn=AsyncMock(),
    )
    fetcher._fetch_from_audiodb = AsyncMock(return_value=None)
    fetcher._fetch_release_group_local_sources = AsyncMock(return_value=None)

    call_count = 0

    async def disconnect_after_two():
        nonlocal call_count
        call_count += 1
        return call_count > 2

    with pytest.raises(ClientDisconnectedError):
        await fetcher.fetch_release_group_cover(
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "500",
            Path("/tmp/test"),
            is_disconnected=disconnect_after_two,
        )
    fetcher._fetch_from_audiodb.assert_awaited_once()


@pytest.mark.anyio
async def test_fetcher_completes_when_disconnect_is_none():
    fetcher = ArtistImageFetcher(
        http_get_fn=AsyncMock(),
        write_cache_fn=AsyncMock(),
        cache=MagicMock(),
    )
    fetcher._fetch_from_audiodb = AsyncMock(return_value=None)
    fetcher._fetch_local_sources = AsyncMock(return_value=(None, False))
    fetcher._fetch_from_wikidata = AsyncMock(return_value=None)

    result = await fetcher.fetch_artist_image(
        "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        None,
        Path("/tmp/test"),
        is_disconnected=None,
    )
    assert result is None
    fetcher._fetch_from_audiodb.assert_awaited_once()
    fetcher._fetch_local_sources.assert_awaited_once()
    fetcher._fetch_from_wikidata.assert_awaited_once()
