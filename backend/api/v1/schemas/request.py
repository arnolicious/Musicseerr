from models.request import QueueItem as QueueItem
from infrastructure.msgspec_fastapi import AppStruct


class AlbumRequest(AppStruct):
    musicbrainz_id: str
    artist: str | None = None
    album: str | None = None
    year: int | None = None


class RequestResponse(AppStruct):
    success: bool
    message: str
    lidarr_response: dict | None = None


class QueueStatusResponse(AppStruct):
    queue_size: int
    processing: bool
