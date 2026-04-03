from typing import Protocol

from models.youtube import YouTubeQuotaResponse


class YouTubeRepositoryProtocol(Protocol):

    def configure(self, api_key: str) -> None:
        ...

    @property
    def is_configured(self) -> bool:
        ...

    @property
    def quota_remaining(self) -> int:
        ...

    async def search_video(self, artist: str, album: str) -> str | None:
        ...

    async def search_track(self, artist: str, track_name: str) -> str | None:
        ...

    def get_quota_status(self) -> YouTubeQuotaResponse:
        ...
