from __future__ import annotations

import logging
import time

from fastapi.responses import Response, StreamingResponse

from repositories.navidrome_models import StreamProxyResult
from repositories.protocols import NavidromeRepositoryProtocol

logger = logging.getLogger(__name__)


class NavidromePlaybackService:
    def __init__(self, navidrome_repo: NavidromeRepositoryProtocol) -> None:
        self._navidrome = navidrome_repo

    def get_stream_url(self, song_id: str) -> str:
        return self._navidrome.build_stream_url(song_id)

    async def proxy_head(self, item_id: str) -> Response:
        """Proxy a HEAD request to Navidrome and return a FastAPI Response."""
        result: StreamProxyResult = await self._navidrome.proxy_head_stream(item_id)
        return Response(status_code=200, headers=result.headers)

    async def proxy_stream(
        self, item_id: str, range_header: str | None = None
    ) -> StreamingResponse:
        """Proxy a GET stream from Navidrome and return a FastAPI StreamingResponse."""
        result: StreamProxyResult = await self._navidrome.proxy_get_stream(
            item_id, range_header=range_header
        )
        return StreamingResponse(
            content=result.body_chunks,
            status_code=result.status_code,
            headers=result.headers,
            media_type=result.media_type,
        )

    async def scrobble(self, song_id: str) -> bool:
        time_ms = int(time.time() * 1000)
        try:
            return await self._navidrome.scrobble(song_id, time_ms=time_ms)
        except Exception:  # noqa: BLE001
            logger.warning("Navidrome scrobble failed for %s", song_id, exc_info=True)
            return False

    async def report_now_playing(self, song_id: str) -> bool:
        try:
            return await self._navidrome.now_playing(song_id)
        except Exception:  # noqa: BLE001
            logger.warning("Navidrome now-playing failed for %s", song_id, exc_info=True)
            return False
