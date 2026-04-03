from infrastructure.msgspec_fastapi import AppStruct


class YouTubeQuotaResponse(AppStruct):
    used: int
    limit: int
    remaining: int
    date: str
