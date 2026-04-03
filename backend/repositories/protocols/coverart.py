from pathlib import Path
from typing import Protocol


class CoverArtRepositoryProtocol(Protocol):

    cache_dir: Path

    async def get_cover_url(
        self,
        album_mbid: str,
        size: str = "500"
    ) -> str | None:
        ...

    async def batch_prefetch_covers(
        self,
        album_mbids: list[str],
        size: str = "250"
    ) -> None:
        ...

    async def delete_covers_for_album(self, album_mbid: str) -> int:
        ...

    async def delete_covers_for_artist(self, artist_mbid: str) -> int:
        ...
