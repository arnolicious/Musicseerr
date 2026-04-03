import time
from typing import Literal

from infrastructure.msgspec_fastapi import AppStruct


class AudioDBArtistResponse(AppStruct):
    idArtist: str
    strArtist: str
    strMusicBrainzID: str | None = None
    strArtistThumb: str | None = None
    strArtistFanart: str | None = None
    strArtistFanart2: str | None = None
    strArtistFanart3: str | None = None
    strArtistFanart4: str | None = None
    strArtistWideThumb: str | None = None
    strArtistBanner: str | None = None
    strArtistLogo: str | None = None
    strArtistCutout: str | None = None
    strArtistClearart: str | None = None


class AudioDBAlbumResponse(AppStruct):
    idAlbum: str
    strAlbum: str
    strMusicBrainzID: str | None = None
    strAlbumThumb: str | None = None
    strAlbumBack: str | None = None
    strAlbumCDart: str | None = None
    strAlbumSpine: str | None = None
    strAlbum3DCase: str | None = None
    strAlbum3DFlat: str | None = None
    strAlbum3DFace: str | None = None
    strAlbum3DThumb: str | None = None


class AudioDBArtistImages(AppStruct):
    thumb_url: str | None = None
    fanart_url: str | None = None
    fanart_url_2: str | None = None
    fanart_url_3: str | None = None
    fanart_url_4: str | None = None
    wide_thumb_url: str | None = None
    banner_url: str | None = None
    logo_url: str | None = None
    cutout_url: str | None = None
    clearart_url: str | None = None
    lookup_source: Literal["mbid", "name"] = "mbid"
    matched_mbid: str | None = None
    is_negative: bool = False
    cached_at: float = 0.0

    @staticmethod
    def from_response(resp: AudioDBArtistResponse, lookup_source: Literal["mbid", "name"] = "mbid") -> "AudioDBArtistImages":
        return AudioDBArtistImages(
            thumb_url=resp.strArtistThumb,
            fanart_url=resp.strArtistFanart,
            fanart_url_2=resp.strArtistFanart2,
            fanart_url_3=resp.strArtistFanart3,
            fanart_url_4=resp.strArtistFanart4,
            wide_thumb_url=resp.strArtistWideThumb,
            banner_url=resp.strArtistBanner,
            logo_url=resp.strArtistLogo,
            cutout_url=resp.strArtistCutout,
            clearart_url=resp.strArtistClearart,
            lookup_source=lookup_source,
            matched_mbid=resp.strMusicBrainzID,
            is_negative=False,
            cached_at=time.time(),
        )

    @classmethod
    def negative(cls, lookup_source: Literal["mbid", "name"] = "mbid") -> "AudioDBArtistImages":
        return cls(
            is_negative=True,
            lookup_source=lookup_source,
            cached_at=time.time(),
        )


class AudioDBAlbumImages(AppStruct):
    album_thumb_url: str | None = None
    album_back_url: str | None = None
    album_cdart_url: str | None = None
    album_spine_url: str | None = None
    album_3d_case_url: str | None = None
    album_3d_flat_url: str | None = None
    album_3d_face_url: str | None = None
    album_3d_thumb_url: str | None = None
    lookup_source: Literal["mbid", "name"] = "mbid"
    matched_mbid: str | None = None
    is_negative: bool = False
    cached_at: float = 0.0

    @staticmethod
    def from_response(resp: AudioDBAlbumResponse, lookup_source: Literal["mbid", "name"] = "mbid") -> "AudioDBAlbumImages":
        return AudioDBAlbumImages(
            album_thumb_url=resp.strAlbumThumb,
            album_back_url=resp.strAlbumBack,
            album_cdart_url=resp.strAlbumCDart,
            album_spine_url=resp.strAlbumSpine,
            album_3d_case_url=resp.strAlbum3DCase,
            album_3d_flat_url=resp.strAlbum3DFlat,
            album_3d_face_url=resp.strAlbum3DFace,
            album_3d_thumb_url=resp.strAlbum3DThumb,
            lookup_source=lookup_source,
            matched_mbid=resp.strMusicBrainzID,
            is_negative=False,
            cached_at=time.time(),
        )

    @classmethod
    def negative(cls, lookup_source: Literal["mbid", "name"] = "mbid") -> "AudioDBAlbumImages":
        return cls(
            is_negative=True,
            lookup_source=lookup_source,
            cached_at=time.time(),
        )
