import json
import sqlite3
import threading
import time

import pytest

from infrastructure.cache.disk_cache import DiskMetadataCache
from infrastructure.persistence.genre_index import GenreIndex
from infrastructure.persistence.library_db import LibraryDB
from infrastructure.persistence.youtube_store import YouTubeStore


def _make_stores(db_path):
    lock = threading.Lock()
    lib = LibraryDB(db_path=db_path, write_lock=lock)
    genre = GenreIndex(db_path=db_path, write_lock=lock)
    yt = YouTubeStore(db_path=db_path, write_lock=lock)
    # All stores must be initialized so cross-domain DELETEs in save_library/clear succeed
    from infrastructure.persistence.mbid_store import MBIDStore
    from infrastructure.persistence.sync_state_store import SyncStateStore

    SyncStateStore(db_path=db_path, write_lock=lock)
    MBIDStore(db_path=db_path, write_lock=lock)
    return lib, genre, yt


@pytest.mark.asyncio
async def test_library_cache_genre_queries_use_normalized_lookup(tmp_path):
    lib, genre, _ = _make_stores(tmp_path / "library.db")

    await lib.save_library(
        artists=[
            {"mbid": "artist-1", "name": "Artist One", "album_count": 1, "date_added": 10},
            {"mbid": "artist-2", "name": "Artist Two", "album_count": 1, "date_added": 20},
        ],
        albums=[
            {
                "mbid": "album-1",
                "artist_mbid": "artist-1",
                "artist_name": "Artist One",
                "title": "First Album",
                "date_added": 100,
                "monitored": True,
            },
            {
                "mbid": "album-2",
                "artist_mbid": "artist-2",
                "artist_name": "Artist Two",
                "title": "Second Album",
                "date_added": 200,
                "monitored": True,
            },
        ],
    )
    await genre.save_artist_genres(
        {
            "artist-1": [" Rock ", "Alternative", "rock"],
            "artist-2": ["Jazz", "rock"],
        }
    )

    artists = await genre.get_artists_by_genre("ROCK", limit=1)
    albums = await genre.get_albums_by_genre(" rock ", limit=2)

    assert [artist["mbid"] for artist in artists] == ["artist-2"]
    assert [album["mbid"] for album in albums] == ["album-2", "album-1"]


@pytest.mark.asyncio
async def test_library_cache_backfills_genre_lookup_from_existing_json_rows(tmp_path):
    db_path = tmp_path / "library.db"
    lib, genre, _ = _make_stores(db_path)
    await lib.save_library(
        artists=[{"mbid": "artist-1", "name": "Artist One", "album_count": 1, "date_added": 10}],
        albums=[],
    )

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM artist_genre_lookup")
        conn.execute(
            "INSERT OR REPLACE INTO artist_genres (artist_mbid_lower, artist_mbid, genres_json) VALUES (?, ?, ?)",
            ("artist-1", "artist-1", json.dumps(["post-rock"])),
        )
        conn.commit()
    finally:
        conn.close()

    _, genre2, _ = _make_stores(db_path)
    artists = await genre2.get_artists_by_genre("POST-ROCK")

    assert [artist["mbid"] for artist in artists] == ["artist-1"]


@pytest.mark.asyncio
async def test_cleanup_expired_covers_removes_expired_cover_payload(tmp_path):
    cache = DiskMetadataCache(base_path=tmp_path)
    cover_dir = tmp_path / "recent" / "covers"
    cover_file = cover_dir / "cover.bin"
    meta_file = cover_dir / "cover.meta.json"

    cover_file.write_bytes(b"image-bytes")
    meta_file.write_text(json.dumps({"expires_at": time.time() - 60, "last_accessed": 1}))

    removed = await cache.cleanup_expired_covers()

    assert removed == 1
    assert not cover_file.exists()
    assert not meta_file.exists()


@pytest.mark.asyncio
async def test_enforce_cover_size_limits_evicts_oldest_recent_cover(tmp_path):
    cache = DiskMetadataCache(base_path=tmp_path)
    cache.recent_covers_max_size_bytes = 6

    cover_dir = tmp_path / "recent" / "covers"
    old_cover = cover_dir / "old.bin"
    new_cover = cover_dir / "new.bin"
    old_meta = cover_dir / "old.meta.json"
    new_meta = cover_dir / "new.meta.json"

    old_cover.write_bytes(b"1234")
    new_cover.write_bytes(b"5678")
    old_meta.write_text(json.dumps({"last_accessed": 1}))
    new_meta.write_text(json.dumps({"last_accessed": 2}))

    freed = await cache.enforce_cover_size_limits()

    assert freed == 4
    assert not old_cover.exists()
    assert not old_meta.exists()
    assert new_cover.exists()
    assert new_meta.exists()


@pytest.mark.asyncio
async def test_library_cache_keeps_youtube_track_links_distinct_per_disc(tmp_path):
    _, _, yt = _make_stores(tmp_path / "library.db")

    await yt.save_youtube_track_links_batch(
        "album-1",
        [
            {
                "track_number": 1,
                "disc_number": 1,
                "album_name": "Album",
                "track_name": "Disc One Track One",
                "video_id": "video-1",
                "artist_name": "Artist",
                "embed_url": "https://example.com/1",
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "track_number": 1,
                "disc_number": 2,
                "album_name": "Album",
                "track_name": "Disc Two Track One",
                "video_id": "video-2",
                "artist_name": "Artist",
                "embed_url": "https://example.com/2",
                "created_at": "2024-01-01T00:00:00Z",
            },
        ],
    )

    links = await yt.get_youtube_track_links("album-1")
    assert [(link["disc_number"], link["track_number"], link["video_id"]) for link in links] == [
        (1, 1, "video-1"),
        (2, 1, "video-2"),
    ]

    await yt.delete_youtube_track_link("album-1", 2, 1)

    remaining = await yt.get_youtube_track_links("album-1")
    assert [(link["disc_number"], link["track_number"], link["video_id"]) for link in remaining] == [
        (1, 1, "video-1")
    ]


@pytest.mark.asyncio
async def test_library_cache_migrates_legacy_youtube_track_links_with_default_disc_number(tmp_path):
    db_path = tmp_path / "library.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE youtube_track_links (
                album_id TEXT NOT NULL,
                track_number INTEGER NOT NULL,
                album_name TEXT NOT NULL,
                track_name TEXT NOT NULL,
                video_id TEXT NOT NULL,
                artist_name TEXT NOT NULL,
                embed_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (album_id, track_number)
            )
            """
        )
        conn.execute(
            """
            INSERT INTO youtube_track_links (
                album_id, track_number, album_name, track_name,
                video_id, artist_name, embed_url, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "album-legacy",
                5,
                "Legacy Album",
                "Legacy Track",
                "legacy-video",
                "Artist",
                "https://example.com/legacy",
                "2024-01-01T00:00:00Z",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    _, _, yt = _make_stores(db_path)
    links = await yt.get_youtube_track_links("album-legacy")

    assert len(links) == 1
    assert links[0]["disc_number"] == 1
    assert links[0]["track_number"] == 5


@pytest.mark.asyncio
async def test_library_cache_youtube_track_links_uniqueness_allows_same_track_different_disc(
    tmp_path,
):
    """Verify the new (album_id, disc_number, track_number) PK allows same track number across discs."""
    _, _, yt = _make_stores(tmp_path / "library.db")

    await yt.save_youtube_track_link(
        album_id="album-uniq",
        track_number=1,
        disc_number=1,
        album_name="Test Album",
        track_name="Track One Disc One",
        video_id="vid-d1t1",
        artist_name="Artist",
        embed_url="https://example.com/d1t1",
        created_at="2024-01-01T00:00:00Z",
    )
    await yt.save_youtube_track_link(
        album_id="album-uniq",
        track_number=1,
        disc_number=2,
        album_name="Test Album",
        track_name="Track One Disc Two",
        video_id="vid-d2t1",
        artist_name="Artist",
        embed_url="https://example.com/d2t1",
        created_at="2024-01-01T00:00:00Z",
    )
    await yt.save_youtube_track_link(
        album_id="album-uniq",
        track_number=1,
        disc_number=1,
        album_name="Test Album",
        track_name="Updated Track One",
        video_id="vid-d1t1-updated",
        artist_name="Artist",
        embed_url="https://example.com/d1t1-v2",
        created_at="2024-01-02T00:00:00Z",
    )

    links = await yt.get_youtube_track_links("album-uniq")
    assert len(links) == 2
    d1 = next(link for link in links if link["disc_number"] == 1)
    d2 = next(link for link in links if link["disc_number"] == 2)
    assert d1["video_id"] == "vid-d1t1-updated"
    assert d1["track_name"] == "Updated Track One"
    assert d2["video_id"] == "vid-d2t1"


@pytest.mark.asyncio
async def test_library_cache_save_single_youtube_track_link_with_disc_number(tmp_path):
    """Verify save_youtube_track_link (single-row path) correctly stores disc_number."""
    _, _, yt = _make_stores(tmp_path / "library.db")

    await yt.save_youtube_track_link(
        album_id="album-single",
        track_number=3,
        disc_number=2,
        album_name="Single Test",
        track_name="Track Three Disc Two",
        video_id="vid-single",
        artist_name="Artist",
        embed_url="https://example.com/single",
        created_at="2024-06-15T00:00:00Z",
    )

    links = await yt.get_youtube_track_links("album-single")
    assert len(links) == 1
    assert links[0]["disc_number"] == 2
    assert links[0]["track_number"] == 3
    assert links[0]["video_id"] == "vid-single"
