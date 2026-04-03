from infrastructure.msgspec_fastapi import AppStruct


class WeeklyExplorationTrack(AppStruct):
    title: str
    artist_name: str
    album_name: str
    recording_mbid: str | None = None
    artist_mbid: str | None = None
    release_group_mbid: str | None = None
    cover_url: str | None = None
    duration_ms: int | None = None


class WeeklyExplorationSection(AppStruct):
    title: str
    playlist_date: str
    tracks: list[WeeklyExplorationTrack] = []
    source_url: str = ""
