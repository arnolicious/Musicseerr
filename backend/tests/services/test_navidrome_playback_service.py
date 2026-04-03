from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.navidrome_playback_service import NavidromePlaybackService


def _make_service(configured: bool = True) -> tuple[NavidromePlaybackService, MagicMock]:
    repo = MagicMock()
    repo.is_configured = MagicMock(return_value=configured)
    repo.build_stream_url = MagicMock(
        return_value="http://navidrome:4533/rest/stream?u=admin&t=tok&s=salt&v=1.16.1&c=musicseerr&f=json&id=song-1"
    )
    repo.scrobble = AsyncMock(return_value=True)
    service = NavidromePlaybackService(navidrome_repo=repo)
    return service, repo


class TestGetStreamUrl:
    def test_delegates_to_repo(self):
        service, repo = _make_service()
        url = service.get_stream_url("song-1")
        repo.build_stream_url.assert_called_once_with("song-1")
        assert "u=admin" in url
        assert "id=song-1" in url

    def test_base_url_correct(self):
        service, _ = _make_service()
        url = service.get_stream_url("song-1")
        assert url.startswith("http://navidrome:4533/rest/stream?")

    def test_raises_when_not_configured(self):
        service, repo = _make_service(configured=False)
        repo.build_stream_url.side_effect = ValueError("Navidrome is not configured")
        with pytest.raises(ValueError, match="not configured"):
            service.get_stream_url("song-1")


class TestScrobble:
    @pytest.mark.asyncio
    async def test_success(self):
        service, repo = _make_service()
        result = await service.scrobble("song-1")
        assert result is True
        repo.scrobble.assert_awaited_once()
        call_args = repo.scrobble.call_args
        assert call_args.args[0] == "song-1"
        assert call_args.kwargs.get("time_ms") is not None

    @pytest.mark.asyncio
    async def test_failure_returns_false(self):
        service, repo = _make_service()
        repo.scrobble = AsyncMock(side_effect=RuntimeError("network"))
        result = await service.scrobble("song-1")
        assert result is False
