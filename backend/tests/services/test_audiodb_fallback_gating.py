from unittest.mock import AsyncMock, MagicMock

import pytest

from repositories.audiodb_models import AudioDBArtistImages, AudioDBAlbumImages
from services.audiodb_image_service import AudioDBImageService


TEST_MBID = "cc197bad-dc9c-440d-a5b5-d52ba2e14234"
TEST_ALBUM_MBID = "1dc4c347-a1db-32aa-b14f-bc9cc507b843"


def _make_settings(
    enabled: bool = True,
    name_search_fallback: bool = False,
) -> MagicMock:
    s = MagicMock()
    s.audiodb_enabled = enabled
    s.audiodb_name_search_fallback = name_search_fallback
    s.cache_ttl_audiodb_found = 604800
    s.cache_ttl_audiodb_not_found = 86400
    s.cache_ttl_audiodb_library = 1209600
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
        repo.get_artist_by_mbid = AsyncMock(return_value=None)
        repo.search_artist_by_name = AsyncMock(return_value=None)
        repo.get_album_by_mbid = AsyncMock(return_value=None)
        repo.search_album_by_name = AsyncMock(return_value=None)
    return AudioDBImageService(
        audiodb_repo=repo,
        disk_cache=disk_cache,
        preferences_service=prefs,
    )


class TestNameSearchFallbackGating:
    @pytest.mark.asyncio
    async def test_monitored_artist_always_gets_fallback(self):
        """Monitored artists get name-search fallback even when setting is False."""
        settings = _make_settings(name_search_fallback=False)
        repo = AsyncMock()
        repo.get_artist_by_mbid = AsyncMock(return_value=None)
        repo.search_artist_by_name = AsyncMock(return_value=None)
        svc = _make_service(settings=settings, repo=repo)

        await svc.fetch_and_cache_artist_images(TEST_MBID, "Coldplay", is_monitored=True)

        repo.search_artist_by_name.assert_called_once_with("Coldplay")

    @pytest.mark.asyncio
    async def test_non_monitored_artist_no_fallback_when_disabled(self):
        """Non-monitored artists don't get fallback when setting is False."""
        settings = _make_settings(name_search_fallback=False)
        repo = AsyncMock()
        repo.get_artist_by_mbid = AsyncMock(return_value=None)
        repo.search_artist_by_name = AsyncMock(return_value=None)
        svc = _make_service(settings=settings, repo=repo)

        await svc.fetch_and_cache_artist_images(TEST_MBID, "Coldplay", is_monitored=False)

        repo.search_artist_by_name.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_monitored_artist_gets_fallback_when_enabled(self):
        """Non-monitored artists get fallback when setting is True."""
        settings = _make_settings(name_search_fallback=True)
        repo = AsyncMock()
        repo.get_artist_by_mbid = AsyncMock(return_value=None)
        repo.search_artist_by_name = AsyncMock(return_value=None)
        svc = _make_service(settings=settings, repo=repo)

        await svc.fetch_and_cache_artist_images(TEST_MBID, "Coldplay", is_monitored=False)

        repo.search_artist_by_name.assert_called_once_with("Coldplay")

    @pytest.mark.asyncio
    async def test_monitored_album_always_gets_fallback(self):
        """Monitored albums get name-search fallback even when setting is False."""
        settings = _make_settings(name_search_fallback=False)
        repo = AsyncMock()
        repo.get_album_by_mbid = AsyncMock(return_value=None)
        repo.search_album_by_name = AsyncMock(return_value=None)
        svc = _make_service(settings=settings, repo=repo)

        await svc.fetch_and_cache_album_images(
            TEST_ALBUM_MBID, artist_name="Coldplay", album_name="Parachutes", is_monitored=True,
        )

        repo.search_album_by_name.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_monitored_album_no_fallback_when_disabled(self):
        """Non-monitored albums don't get fallback when setting is False."""
        settings = _make_settings(name_search_fallback=False)
        repo = AsyncMock()
        repo.get_album_by_mbid = AsyncMock(return_value=None)
        repo.search_album_by_name = AsyncMock(return_value=None)
        svc = _make_service(settings=settings, repo=repo)

        await svc.fetch_and_cache_album_images(
            TEST_ALBUM_MBID, artist_name="Coldplay", album_name="Parachutes", is_monitored=False,
        )

        repo.search_album_by_name.assert_not_called()


class TestNameSearchFallbackWithCachedNegative:
    @pytest.mark.asyncio
    async def test_monitored_retries_with_name_on_mbid_negative(self):
        """When cached negative is from MBID lookup, monitored items retry with name."""
        settings = _make_settings(name_search_fallback=False)
        negative = AudioDBArtistImages.negative(lookup_source="mbid")
        disk_cache = AsyncMock()
        disk_cache.get_audiodb_artist = AsyncMock(return_value=negative)
        disk_cache.set_audiodb_artist = AsyncMock()
        repo = AsyncMock()
        repo.search_artist_by_name = AsyncMock(return_value=None)
        svc = _make_service(settings=settings, disk_cache=disk_cache, repo=repo)

        await svc.fetch_and_cache_artist_images(TEST_MBID, "Coldplay", is_monitored=True)

        repo.search_artist_by_name.assert_called_once_with("Coldplay")

    @pytest.mark.asyncio
    async def test_non_monitored_skips_name_retry_on_mbid_negative(self):
        """When cached negative is from MBID lookup, non-monitored items skip name retry (setting=False)."""
        settings = _make_settings(name_search_fallback=False)
        negative = AudioDBArtistImages.negative(lookup_source="mbid")
        disk_cache = AsyncMock()
        disk_cache.get_audiodb_artist = AsyncMock(return_value=negative)
        disk_cache.set_audiodb_artist = AsyncMock()
        repo = AsyncMock()
        repo.search_artist_by_name = AsyncMock(return_value=None)
        svc = _make_service(settings=settings, disk_cache=disk_cache, repo=repo)

        await svc.fetch_and_cache_artist_images(TEST_MBID, "Coldplay", is_monitored=False)

        repo.search_artist_by_name.assert_not_called()
