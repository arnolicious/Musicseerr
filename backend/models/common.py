from typing import Literal

from infrastructure.msgspec_fastapi import AppStruct


class ServiceStatus(AppStruct):
    status: Literal["ok", "error"]
    version: str | None = None
    message: str | None = None
