from __future__ import annotations

from infrastructure.msgspec_fastapi import AppStruct


class NavidromeTrackInfo(AppStruct):
    navidrome_id: str
    title: str
    track_number: int
    duration_seconds: float
    disc_number: int = 1
    album_name: str = ""
    artist_name: str = ""
    codec: str | None = None
    bitrate: int | None = None


class NavidromeAlbumSummary(AppStruct):
    navidrome_id: str
    name: str
    artist_name: str = ""
    year: int | None = None
    track_count: int = 0
    image_url: str | None = None
    musicbrainz_id: str | None = None
    artist_musicbrainz_id: str | None = None


class NavidromeAlbumDetail(AppStruct):
    navidrome_id: str
    name: str
    artist_name: str = ""
    year: int | None = None
    track_count: int = 0
    image_url: str | None = None
    musicbrainz_id: str | None = None
    artist_musicbrainz_id: str | None = None
    tracks: list[NavidromeTrackInfo] = []


class NavidromeAlbumMatch(AppStruct):
    found: bool
    navidrome_album_id: str | None = None
    tracks: list[NavidromeTrackInfo] = []


class NavidromeArtistSummary(AppStruct):
    navidrome_id: str
    name: str
    image_url: str | None = None
    album_count: int = 0
    musicbrainz_id: str | None = None


class NavidromeLibraryStats(AppStruct):
    total_tracks: int = 0
    total_albums: int = 0
    total_artists: int = 0


class NavidromeSearchResponse(AppStruct):
    albums: list[NavidromeAlbumSummary] = []
    artists: list[NavidromeArtistSummary] = []
    tracks: list[NavidromeTrackInfo] = []


class NavidromeAlbumPage(AppStruct):
    items: list[NavidromeAlbumSummary] = []
    total: int = 0
