import time
from unittest.mock import AsyncMock, MagicMock

import msgspec
import pytest

from repositories.audiodb_models import (
    AudioDBArtistImages,
    AudioDBArtistResponse,
)
from services.audiodb_image_service import AudioDBImageService

SAMPLE_ARTIST_RESP = AudioDBArtistResponse(
    idArtist="111239",
    strArtist="Coldplay",
    strMusicBrainzID="cc197bad-dc9c-440d-a5b5-d52ba2e14234",
    strArtistThumb="https://example.com/thumb.jpg",
    strArtistFanart="https://example.com/fanart.jpg",
)

TEST_MBID = "cc197bad-dc9c-440d-a5b5-d52ba2e14234"


def _make_settings(
    enabled: bool = True,
    name_search_fallback: bool = False,
    ttl_found: int = 604800,
    ttl_not_found: int = 86400,
    ttl_library: int = 1209600,
) -> MagicMock:
    s = MagicMock()
    s.audiodb_enabled = enabled
    s.audiodb_name_search_fallback = name_search_fallback
    s.cache_ttl_audiodb_found = ttl_found
    s.cache_ttl_audiodb_not_found = ttl_not_found
    s.cache_ttl_audiodb_library = ttl_library
    return s


def _make_service(
    settings: MagicMock | None = None,
    disk_cache: AsyncMock | None = None,
    repo: AsyncMock | None = None,
) -> AudioDBImageService:
    if settings is None:
        settings = _make_settings()
    prefs = MagicMock()
    prefs.get_advanced_settings.return_value = settings
    if disk_cache is None:
        disk_cache = AsyncMock()
        disk_cache.get_audiodb_artist = AsyncMock(return_value=None)
        disk_cache.get_audiodb_album = AsyncMock(return_value=None)
        disk_cache.set_audiodb_artist = AsyncMock()
        disk_cache.set_audiodb_album = AsyncMock()
    if repo is None:
        repo = AsyncMock()
    return AudioDBImageService(
        audiodb_repo=repo,
        disk_cache=disk_cache,
        preferences_service=prefs,
        memory_cache=None,
    )


class TestNegativeCacheExpiry:
    @pytest.mark.asyncio
    async def test_negative_entry_cached_with_correct_structure(self):
        """MBID miss produces a negative entry with the right shape and TTL."""
        disk = AsyncMock()
        disk.get_audiodb_artist = AsyncMock(return_value=None)
        disk.set_audiodb_artist = AsyncMock()
        repo = AsyncMock()
        repo.get_artist_by_mbid = AsyncMock(return_value=None)
        ttl_not_found = 86400
        svc = _make_service(
            settings=_make_settings(ttl_not_found=ttl_not_found),
            disk_cache=disk,
            repo=repo,
        )

        before = time.time()
        await svc.fetch_and_cache_artist_images(TEST_MBID, name="Coldplay")

        disk.set_audiodb_artist.assert_awaited()
        call_kwargs = disk.set_audiodb_artist.call_args
        cached_entry: AudioDBArtistImages = call_kwargs[0][1]
        ttl_arg = call_kwargs.kwargs.get("ttl_seconds", call_kwargs[1].get("ttl_seconds") if len(call_kwargs) > 1 and isinstance(call_kwargs[1], dict) else None)

        assert cached_entry.is_negative is True
        assert cached_entry.lookup_source == "mbid"
        assert cached_entry.cached_at >= before
        assert cached_entry.cached_at <= time.time() + 5
        assert cached_entry.thumb_url is None
        assert cached_entry.fanart_url is None
        assert cached_entry.wide_thumb_url is None
        assert cached_entry.banner_url is None
        assert cached_entry.logo_url is None
        assert cached_entry.cutout_url is None
        assert cached_entry.clearart_url is None
        assert ttl_arg == ttl_not_found

    @pytest.mark.asyncio
    async def test_valid_negative_entry_prevents_api_call(self):
        """A fresh negative cache entry prevents re-fetching from AudioDB."""
        negative = AudioDBArtistImages.negative(lookup_source="mbid")
        raw = msgspec.structs.asdict(negative)
        disk = AsyncMock()
        disk.get_audiodb_artist = AsyncMock(return_value=raw)
        disk.set_audiodb_artist = AsyncMock()
        repo = AsyncMock()
        repo.get_artist_by_mbid = AsyncMock(return_value=None)
        svc = _make_service(
            settings=_make_settings(name_search_fallback=False),
            disk_cache=disk,
            repo=repo,
        )

        result = await svc.fetch_and_cache_artist_images(TEST_MBID)

        assert result is not None
        assert result.is_negative is True
        repo.get_artist_by_mbid.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_expired_negative_entry_triggers_refetch(self):
        """When the disk cache returns None for an expired/evicted negative
        entry, a fresh API call is made and the cache is updated."""
        expired_negative = AudioDBArtistImages.negative(lookup_source="mbid")
        expired_negative = AudioDBArtistImages(
            is_negative=True,
            lookup_source="mbid",
            cached_at=time.time() - 200_000,
        )
        disk = AsyncMock()
        disk.get_audiodb_artist = AsyncMock(return_value=None)
        disk.set_audiodb_artist = AsyncMock()
        repo = AsyncMock()
        repo.get_artist_by_mbid = AsyncMock(return_value=SAMPLE_ARTIST_RESP)
        svc = _make_service(disk_cache=disk, repo=repo)

        result = await svc.fetch_and_cache_artist_images(TEST_MBID, name="Coldplay")

        assert result is not None
        assert result.is_negative is False
        assert result.thumb_url == "https://example.com/thumb.jpg"
        assert result.lookup_source == "mbid"
        repo.get_artist_by_mbid.assert_awaited_once_with(TEST_MBID)
        disk.set_audiodb_artist.assert_awaited_once()
        written_entry: AudioDBArtistImages = disk.set_audiodb_artist.call_args[0][1]
        assert written_entry.is_negative is False
        assert written_entry.thumb_url == "https://example.com/thumb.jpg"

    @pytest.mark.asyncio
    async def test_mbid_negative_triggers_name_search_when_enabled(self):
        """A cached MBID-negative entry skips MBID lookup and falls back to
        name search when audiodb_name_search_fallback is enabled."""
        negative = AudioDBArtistImages.negative(lookup_source="mbid")
        raw = msgspec.structs.asdict(negative)
        disk = AsyncMock()
        disk.get_audiodb_artist = AsyncMock(return_value=raw)
        disk.set_audiodb_artist = AsyncMock()
        repo = AsyncMock()
        repo.get_artist_by_mbid = AsyncMock(return_value=None)
        repo.search_artist_by_name = AsyncMock(return_value=SAMPLE_ARTIST_RESP)
        svc = _make_service(
            settings=_make_settings(name_search_fallback=True),
            disk_cache=disk,
            repo=repo,
        )

        result = await svc.fetch_and_cache_artist_images(TEST_MBID, name="Coldplay")

        assert result is not None
        assert result.is_negative is False
        assert result.lookup_source == "name"
        assert result.thumb_url == "https://example.com/thumb.jpg"
        repo.get_artist_by_mbid.assert_not_awaited()
        repo.search_artist_by_name.assert_awaited_once_with("Coldplay")
        disk.set_audiodb_artist.assert_awaited()
        final_entry: AudioDBArtistImages = disk.set_audiodb_artist.call_args[0][1]
        assert final_entry.lookup_source == "name"
        assert final_entry.is_negative is False

    @pytest.mark.asyncio
    async def test_mbid_negative_no_name_search_when_disabled(self):
        """A cached MBID-negative entry is returned as-is when name-search
        fallback is disabled and the caller is not monitored."""
        negative = AudioDBArtistImages.negative(lookup_source="mbid")
        raw = msgspec.structs.asdict(negative)
        disk = AsyncMock()
        disk.get_audiodb_artist = AsyncMock(return_value=raw)
        disk.set_audiodb_artist = AsyncMock()
        repo = AsyncMock()
        repo.get_artist_by_mbid = AsyncMock(return_value=None)
        repo.search_artist_by_name = AsyncMock(return_value=None)
        svc = _make_service(
            settings=_make_settings(name_search_fallback=False),
            disk_cache=disk,
            repo=repo,
        )

        result = await svc.fetch_and_cache_artist_images(
            TEST_MBID, name="Coldplay", is_monitored=False,
        )

        assert result is not None
        assert result.is_negative is True
        repo.search_artist_by_name.assert_not_awaited()
