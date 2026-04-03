import time

import msgspec
import pytest

from repositories.audiodb_models import (
    AudioDBArtistImages,
    AudioDBArtistResponse,
    AudioDBAlbumImages,
    AudioDBAlbumResponse,
)


def test_artist_images_serialization_roundtrip():
    now = time.time()
    original = AudioDBArtistImages(
        thumb_url="https://cdn.example.com/thumb.jpg",
        fanart_url="https://cdn.example.com/fanart.jpg",
        fanart_url_2="https://cdn.example.com/fanart2.jpg",
        fanart_url_3="https://cdn.example.com/fanart3.jpg",
        fanart_url_4="https://cdn.example.com/fanart4.jpg",
        wide_thumb_url="https://cdn.example.com/wide.jpg",
        banner_url="https://cdn.example.com/banner.jpg",
        logo_url="https://cdn.example.com/logo.jpg",
        cutout_url="https://cdn.example.com/cutout.jpg",
        clearart_url="https://cdn.example.com/clearart.jpg",
        lookup_source="mbid",
        matched_mbid="abc-123",
        is_negative=False,
        cached_at=now,
    )
    data = msgspec.json.encode(original)
    decoded = msgspec.json.decode(data, type=AudioDBArtistImages)

    assert decoded.thumb_url == original.thumb_url
    assert decoded.fanart_url == original.fanart_url
    assert decoded.fanart_url_2 == original.fanart_url_2
    assert decoded.fanart_url_3 == original.fanart_url_3
    assert decoded.fanart_url_4 == original.fanart_url_4
    assert decoded.wide_thumb_url == original.wide_thumb_url
    assert decoded.banner_url == original.banner_url
    assert decoded.logo_url == original.logo_url
    assert decoded.cutout_url == original.cutout_url
    assert decoded.clearart_url == original.clearart_url
    assert decoded.lookup_source == "mbid"
    assert decoded.matched_mbid == "abc-123"
    assert decoded.is_negative is False
    assert decoded.cached_at == now


def test_artist_images_negative_entry_roundtrip():
    original = AudioDBArtistImages(
        is_negative=True,
        lookup_source="mbid",
        cached_at=time.time(),
    )
    data = msgspec.json.encode(original)
    decoded = msgspec.json.decode(data, type=AudioDBArtistImages)

    assert decoded.is_negative is True
    assert decoded.thumb_url is None
    assert decoded.fanart_url is None
    assert decoded.fanart_url_2 is None
    assert decoded.fanart_url_3 is None
    assert decoded.fanart_url_4 is None
    assert decoded.wide_thumb_url is None
    assert decoded.banner_url is None
    assert decoded.logo_url is None
    assert decoded.cutout_url is None
    assert decoded.clearart_url is None


def test_album_images_serialization_roundtrip():
    now = time.time()
    original = AudioDBAlbumImages(
        album_thumb_url="https://cdn.example.com/album_thumb.jpg",
        album_back_url="https://cdn.example.com/album_back.jpg",
        album_cdart_url="https://cdn.example.com/album_cdart.jpg",
        album_spine_url="https://cdn.example.com/album_spine.jpg",
        album_3d_case_url="https://cdn.example.com/album_3d_case.jpg",
        album_3d_flat_url="https://cdn.example.com/album_3d_flat.jpg",
        album_3d_face_url="https://cdn.example.com/album_3d_face.jpg",
        album_3d_thumb_url="https://cdn.example.com/album_3d_thumb.jpg",
        lookup_source="mbid",
        matched_mbid="album-456",
        is_negative=False,
        cached_at=now,
    )
    data = msgspec.json.encode(original)
    decoded = msgspec.json.decode(data, type=AudioDBAlbumImages)

    assert decoded.album_thumb_url == original.album_thumb_url
    assert decoded.album_back_url == original.album_back_url
    assert decoded.album_cdart_url == original.album_cdart_url
    assert decoded.album_spine_url == original.album_spine_url
    assert decoded.album_3d_case_url == original.album_3d_case_url
    assert decoded.album_3d_flat_url == original.album_3d_flat_url
    assert decoded.album_3d_face_url == original.album_3d_face_url
    assert decoded.album_3d_thumb_url == original.album_3d_thumb_url
    assert decoded.lookup_source == "mbid"
    assert decoded.matched_mbid == "album-456"
    assert decoded.is_negative is False
    assert decoded.cached_at == now


def test_album_images_negative_entry_roundtrip():
    original = AudioDBAlbumImages(
        is_negative=True,
        lookup_source="mbid",
        cached_at=time.time(),
    )
    data = msgspec.json.encode(original)
    decoded = msgspec.json.decode(data, type=AudioDBAlbumImages)

    assert decoded.is_negative is True
    assert decoded.album_thumb_url is None
    assert decoded.album_back_url is None
    assert decoded.album_cdart_url is None
    assert decoded.album_spine_url is None
    assert decoded.album_3d_case_url is None
    assert decoded.album_3d_flat_url is None
    assert decoded.album_3d_face_url is None
    assert decoded.album_3d_thumb_url is None


def test_artist_images_name_lookup_source():
    original = AudioDBArtistImages(
        lookup_source="name",
        matched_mbid="different-mbid",
        cached_at=time.time(),
    )
    data = msgspec.json.encode(original)
    decoded = msgspec.json.decode(data, type=AudioDBArtistImages)

    assert decoded.lookup_source == "name"
    assert decoded.matched_mbid == "different-mbid"


def test_artist_response_from_full_payload():
    resp = AudioDBArtistResponse(
        idArtist="112345",
        strArtist="Test Artist",
        strMusicBrainzID="mbid-artist-001",
        strArtistThumb="https://cdn.example.com/thumb.jpg",
        strArtistFanart="https://cdn.example.com/fanart.jpg",
        strArtistFanart2="https://cdn.example.com/fanart2.jpg",
        strArtistFanart3="https://cdn.example.com/fanart3.jpg",
        strArtistFanart4="https://cdn.example.com/fanart4.jpg",
        strArtistWideThumb="https://cdn.example.com/wide.jpg",
        strArtistBanner="https://cdn.example.com/banner.jpg",
        strArtistLogo="https://cdn.example.com/logo.jpg",
        strArtistCutout="https://cdn.example.com/cutout.jpg",
        strArtistClearart="https://cdn.example.com/clearart.jpg",
    )
    images = AudioDBArtistImages.from_response(resp, lookup_source="mbid")

    assert images.thumb_url == "https://cdn.example.com/thumb.jpg"
    assert images.fanart_url == "https://cdn.example.com/fanart.jpg"
    assert images.fanart_url_2 == "https://cdn.example.com/fanart2.jpg"
    assert images.fanart_url_3 == "https://cdn.example.com/fanart3.jpg"
    assert images.fanart_url_4 == "https://cdn.example.com/fanart4.jpg"
    assert images.wide_thumb_url == "https://cdn.example.com/wide.jpg"
    assert images.banner_url == "https://cdn.example.com/banner.jpg"
    assert images.logo_url == "https://cdn.example.com/logo.jpg"
    assert images.cutout_url == "https://cdn.example.com/cutout.jpg"
    assert images.clearart_url == "https://cdn.example.com/clearart.jpg"
    assert images.is_negative is False
    assert images.matched_mbid == "mbid-artist-001"


def test_album_response_from_full_payload():
    resp = AudioDBAlbumResponse(
        idAlbum="998877",
        strAlbum="Test Album",
        strMusicBrainzID="mbid-album-001",
        strAlbumThumb="https://cdn.example.com/album_thumb.jpg",
        strAlbumBack="https://cdn.example.com/album_back.jpg",
        strAlbumCDart="https://cdn.example.com/album_cdart.jpg",
        strAlbumSpine="https://cdn.example.com/album_spine.jpg",
        strAlbum3DCase="https://cdn.example.com/album_3d_case.jpg",
        strAlbum3DFlat="https://cdn.example.com/album_3d_flat.jpg",
        strAlbum3DFace="https://cdn.example.com/album_3d_face.jpg",
        strAlbum3DThumb="https://cdn.example.com/album_3d_thumb.jpg",
    )
    images = AudioDBAlbumImages.from_response(resp, lookup_source="mbid")

    assert images.album_thumb_url == "https://cdn.example.com/album_thumb.jpg"
    assert images.album_back_url == "https://cdn.example.com/album_back.jpg"
    assert images.album_cdart_url == "https://cdn.example.com/album_cdart.jpg"
    assert images.album_spine_url == "https://cdn.example.com/album_spine.jpg"
    assert images.album_3d_case_url == "https://cdn.example.com/album_3d_case.jpg"
    assert images.album_3d_flat_url == "https://cdn.example.com/album_3d_flat.jpg"
    assert images.album_3d_face_url == "https://cdn.example.com/album_3d_face.jpg"
    assert images.album_3d_thumb_url == "https://cdn.example.com/album_3d_thumb.jpg"
    assert images.is_negative is False
    assert images.matched_mbid == "mbid-album-001"


def test_artist_negative_factory():
    before = time.time()
    result = AudioDBArtistImages.negative(lookup_source="mbid")
    after = time.time()

    assert result.is_negative is True
    assert result.lookup_source == "mbid"
    assert result.thumb_url is None
    assert result.fanart_url is None
    assert result.fanart_url_2 is None
    assert result.fanart_url_3 is None
    assert result.fanart_url_4 is None
    assert result.wide_thumb_url is None
    assert result.banner_url is None
    assert result.logo_url is None
    assert result.cutout_url is None
    assert result.clearart_url is None
    assert before <= result.cached_at <= after


def test_artist_negative_factory_name_source():
    result = AudioDBArtistImages.negative(lookup_source="name")

    assert result.lookup_source == "name"


def test_album_negative_factory():
    before = time.time()
    result = AudioDBAlbumImages.negative(lookup_source="mbid")
    after = time.time()

    assert result.is_negative is True
    assert result.lookup_source == "mbid"
    assert result.album_thumb_url is None
    assert result.album_back_url is None
    assert result.album_cdart_url is None
    assert result.album_spine_url is None
    assert result.album_3d_case_url is None
    assert result.album_3d_flat_url is None
    assert result.album_3d_face_url is None
    assert result.album_3d_thumb_url is None
    assert before <= result.cached_at <= after


def test_artist_response_tolerates_unknown_fields():
    data = b'{"idArtist": "1", "strArtist": "Test", "strNewUnknownField": "value"}'
    resp = msgspec.json.decode(data, type=AudioDBArtistResponse)

    assert resp.idArtist == "1"
    assert resp.strArtist == "Test"


def test_album_response_tolerates_unknown_fields():
    data = b'{"idAlbum": "1", "strAlbum": "Test", "strNewUnknownField": "value"}'
    resp = msgspec.json.decode(data, type=AudioDBAlbumResponse)

    assert resp.idAlbum == "1"
    assert resp.strAlbum == "Test"


REAL_ARTIST_PAYLOAD = {
    "idArtist": "111239",
    "strArtist": "Coldplay",
    "strMusicBrainzID": "cc197bad-dc9c-440d-a5b5-d52ba2e14234",
    "strArtistThumb": "https://r2.theaudiodb.com/images/artist/thumb/coldplay.jpg",
    "strArtistFanart": "https://r2.theaudiodb.com/images/artist/fanart/coldplay1.jpg",
    "strArtistFanart2": "https://r2.theaudiodb.com/images/artist/fanart/coldplay2.jpg",
    "strArtistFanart3": None,
    "strArtistFanart4": None,
    "strArtistWideThumb": "https://r2.theaudiodb.com/images/artist/widethumb/coldplay.jpg",
    "strArtistBanner": "https://r2.theaudiodb.com/images/artist/banner/coldplay.jpg",
    "strArtistLogo": None,
    "strArtistCutout": None,
    "strArtistClearart": None,
    "strArtistStripped": None,
    "strArtistAlternate": "",
    "strLabel": "Parlophone",
    "idLabel": "45114",
    "intFormedYear": "1996",
    "intBornYear": "1996",
    "intDiedYear": None,
    "strDisbanded": None,
    "strStyle": "Rock/Pop",
    "strGenre": "Alternative Rock",
    "strMood": "Happy",
    "strWebsite": "www.coldplay.com",
    "strFacebook": "",
    "strTwitter": "",
    "strBiographyEN": "Coldplay are a British rock band...",
    "strGender": "Male",
    "intMembers": "4",
    "strCountry": "London, England",
    "strCountryCode": "GB",
    "strArtistFanart5": None,
    "strArtistFanart6": None,
}

REAL_ALBUM_PAYLOAD = {
    "idAlbum": "2115888",
    "strAlbum": "Parachutes",
    "strMusicBrainzID": "1dc4c347-a1db-32aa-b14f-bc9cc507b843",
    "strAlbumThumb": "https://r2.theaudiodb.com/images/album/thumb/parachutes.jpg",
    "strAlbumBack": "https://r2.theaudiodb.com/images/album/back/parachutes.jpg",
    "strAlbumCDart": None,
    "strAlbumSpine": None,
    "strAlbum3DCase": None,
    "strAlbum3DFlat": None,
    "strAlbum3DFace": None,
    "strAlbum3DThumb": None,
    "idArtist": "111239",
    "idLabel": "45114",
    "strArtist": "Coldplay",
    "intYearReleased": "2000",
    "strStyle": "Rock/Pop",
    "strGenre": "Alternative Rock",
    "strLabel": "Parlophone",
    "strReleaseFormat": "Album",
    "intSales": "0",
    "strAlbumStripped": "Parachutes",
    "strDescriptionEN": "Parachutes is the debut studio album...",
    "intScore": "8",
    "intScoreVotes": "5",
    "strLocked": "unlocked",
}


def test_real_artist_payload_decodes_to_response():
    """8.1.f — Decode a real-shape AudioDB artist payload with unknown fields."""
    data = msgspec.json.encode(REAL_ARTIST_PAYLOAD)
    resp = msgspec.json.decode(data, type=AudioDBArtistResponse)

    assert resp.idArtist == "111239"
    assert resp.strArtist == "Coldplay"
    assert resp.strMusicBrainzID == "cc197bad-dc9c-440d-a5b5-d52ba2e14234"
    assert resp.strArtistThumb == "https://r2.theaudiodb.com/images/artist/thumb/coldplay.jpg"
    assert resp.strArtistFanart == "https://r2.theaudiodb.com/images/artist/fanart/coldplay1.jpg"
    assert resp.strArtistFanart2 == "https://r2.theaudiodb.com/images/artist/fanart/coldplay2.jpg"
    assert resp.strArtistFanart3 is None
    assert resp.strArtistWideThumb == "https://r2.theaudiodb.com/images/artist/widethumb/coldplay.jpg"
    assert resp.strArtistBanner == "https://r2.theaudiodb.com/images/artist/banner/coldplay.jpg"

    images = AudioDBArtistImages.from_response(resp, lookup_source="mbid")
    assert images.thumb_url == resp.strArtistThumb
    assert images.fanart_url == resp.strArtistFanart
    assert images.is_negative is False
    assert images.matched_mbid == "cc197bad-dc9c-440d-a5b5-d52ba2e14234"


def test_real_album_payload_decodes_to_response():
    """8.1.f — Decode a real-shape AudioDB album payload with unknown fields."""
    data = msgspec.json.encode(REAL_ALBUM_PAYLOAD)
    resp = msgspec.json.decode(data, type=AudioDBAlbumResponse)

    assert resp.idAlbum == "2115888"
    assert resp.strAlbum == "Parachutes"
    assert resp.strMusicBrainzID == "1dc4c347-a1db-32aa-b14f-bc9cc507b843"
    assert resp.strAlbumThumb == "https://r2.theaudiodb.com/images/album/thumb/parachutes.jpg"
    assert resp.strAlbumBack == "https://r2.theaudiodb.com/images/album/back/parachutes.jpg"
    assert resp.strAlbumCDart is None

    images = AudioDBAlbumImages.from_response(resp, lookup_source="mbid")
    assert images.album_thumb_url == resp.strAlbumThumb
    assert images.album_back_url == resp.strAlbumBack
    assert images.is_negative is False
    assert images.matched_mbid == "1dc4c347-a1db-32aa-b14f-bc9cc507b843"
