from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from repositories.navidrome_models import (
    SubsonicAlbum,
    SubsonicArtist,
    SubsonicGenre,
    SubsonicPlaylist,
    SubsonicSearchResult,
    SubsonicSong,
)

if TYPE_CHECKING:
    from repositories.navidrome_models import StreamProxyResult


class NavidromeRepositoryProtocol(Protocol):

    def is_configured(self) -> bool:
        ...

    def configure(self, url: str, username: str, password: str) -> None:
        ...

    async def ping(self) -> bool:
        ...

    async def get_album_list(
        self, type: str, size: int = 20, offset: int = 0, genre: str | None = None
    ) -> list[SubsonicAlbum]:
        ...

    async def get_album(self, id: str) -> SubsonicAlbum:
        ...

    async def get_artists(self) -> list[SubsonicArtist]:
        ...

    async def get_artist(self, id: str) -> SubsonicArtist:
        ...

    async def get_song(self, id: str) -> SubsonicSong:
        ...

    async def search(
        self,
        query: str,
        artist_count: int = 20,
        album_count: int = 20,
        song_count: int = 20,
    ) -> SubsonicSearchResult:
        ...

    async def get_starred(self) -> SubsonicSearchResult:
        ...

    async def get_genres(self) -> list[SubsonicGenre]:
        ...

    async def get_playlists(self) -> list[SubsonicPlaylist]:
        ...

    async def get_playlist(self, id: str) -> SubsonicPlaylist:
        ...

    async def get_random_songs(
        self, size: int = 20, genre: str | None = None
    ) -> list[SubsonicSong]:
        ...

    async def scrobble(self, id: str, time_ms: int | None = None) -> bool:
        ...

    async def validate_connection(self) -> tuple[bool, str]:
        ...

    async def clear_cache(self) -> None:
        ...

    def build_stream_url(self, song_id: str) -> str:
        ...

    async def proxy_head_stream(self, song_id: str) -> StreamProxyResult:
        ...

    async def proxy_get_stream(
        self, song_id: str, range_header: str | None = None
    ) -> StreamProxyResult:
        ...

    async def now_playing(self, id: str) -> bool:
        ...
