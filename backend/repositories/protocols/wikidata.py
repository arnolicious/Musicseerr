from typing import Protocol


class WikidataRepositoryProtocol(Protocol):

    async def get_artist_bio(self, artist_mbid: str) -> str | None:
        ...

    async def get_artist_image(self, artist_mbid: str) -> str | None:
        ...
