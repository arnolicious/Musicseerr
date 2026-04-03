from datetime import datetime
from typing import Annotated

import msgspec

from infrastructure.msgspec_fastapi import AppStruct


class QueueItem(AppStruct):
    artist: str
    album: str
    status: str
    progress: Annotated[int, msgspec.Meta(ge=0, le=100)] | None = None
    eta: datetime | None = None
    musicbrainz_id: str | None = None
