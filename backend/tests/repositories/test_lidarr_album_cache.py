import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from core.config import Settings
from infrastructure.cache.memory_cache import InMemoryCache
from repositories.lidarr.album import LidarrAlbumRepository


def _make_settings() -> Settings:
    settings = MagicMock(spec=Settings)
    settings.lidarr_url = "http://localhost:8686"
    settings.lidarr_api_key = "test-key"
    settings.quality_profile_id = 1
    return settings


def _sample_album_data() -> list[dict]:
    return [
        {
            "id": 1,
            "title": "Album One",
            "foreignAlbumId": "aaaa-bbbb-cccc",
            "monitored": True,
            "images": [],
            "artist": {
                "artistName": "Artist A",
                "foreignArtistId": "artist-a-mbid",
            },
        }
    ]


@pytest.fixture
def cache():
    return InMemoryCache(max_entries=100)


@pytest.fixture
def repo(cache):
    settings = _make_settings()
    http_client = AsyncMock(spec=httpx.AsyncClient)
    return LidarrAlbumRepository(settings=settings, http_client=http_client, cache=cache)


class TestGetAllAlbumsCache:
    @pytest.mark.asyncio
    async def test_get_all_albums_uses_shared_raw_cache(self, repo):
        with patch.object(repo, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _sample_album_data()

            first = await repo.get_all_albums()
            second = await repo.get_all_albums()

            assert mock_get.await_count == 1
            assert first == second
            assert len(first) == 1


class TestAlbumMutationInvalidation:
    @pytest.mark.asyncio
    async def test_delete_album_invalidates_shared_and_derived_album_cache(self, repo):
        with patch.object(repo, "_get", new_callable=AsyncMock) as mock_get, patch.object(
            repo, "_delete", new_callable=AsyncMock
        ) as mock_delete:
            mock_get.return_value = _sample_album_data()
            mock_delete.return_value = None

            await repo.get_all_albums()
            assert mock_get.await_count == 1

            deleted = await repo.delete_album(album_id=1, delete_files=False)
            assert deleted is True
            assert mock_delete.await_count == 1

            await repo.get_all_albums()
            assert mock_get.await_count == 2


class TestGetAlbumTracksCoercion:
    """Regression: Lidarr returns trackNumber as a string; get_album_tracks must coerce to int."""

    @pytest.mark.asyncio
    async def test_string_track_numbers_coerced_to_int(self, repo):
        raw_tracks = [
            {
                "trackNumber": "3",
                "absoluteTrackNumber": 3,
                "mediumNumber": "1",
                "title": "Speed Kills",
                "duration": 230000,
                "trackFileId": 2618,
                "hasFile": True,
            },
            {
                "trackNumber": "10",
                "absoluteTrackNumber": 10,
                "mediumNumber": 1,
                "title": "Fresh Air",
                "duration": 180000,
                "trackFileId": 2625,
                "hasFile": True,
            },
        ]
        with patch.object(repo, "_get", new_callable=AsyncMock, return_value=raw_tracks):
            result = await repo.get_album_tracks(album_id=52)

        assert len(result) == 2
        assert all(isinstance(t["track_number"], int) for t in result)
        assert all(isinstance(t["disc_number"], int) for t in result)
        assert result[0]["track_number"] == 3
        assert result[1]["track_number"] == 10
        # Verify sorting is numeric (3 before 10), not lexicographic ("10" before "3")
        assert result[0]["title"] == "Speed Kills"
        assert result[1]["title"] == "Fresh Air"
