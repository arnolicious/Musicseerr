import asyncio
import logging
from typing import Any
from urllib.parse import quote_plus

from api.v1.schemas.discover import DiscoverQueueEnrichment
from infrastructure.cache.cache_keys import DISCOVER_QUEUE_ENRICH_PREFIX
from infrastructure.cache.memory_cache import CacheInterface
from infrastructure.validators import clean_lastfm_bio
from repositories.protocols import (
    ListenBrainzRepositoryProtocol,
    MusicBrainzRepositoryProtocol,
    LastFmRepositoryProtocol,
)
from services.discover.integration_helpers import IntegrationHelpers

logger = logging.getLogger(__name__)


class QueueEnrichmentService:
    def __init__(
        self,
        musicbrainz_repo: MusicBrainzRepositoryProtocol,
        listenbrainz_repo: ListenBrainzRepositoryProtocol,
        preferences_service: Any,
        integration: IntegrationHelpers,
        memory_cache: CacheInterface | None = None,
        wikidata_repo: Any = None,
        lastfm_repo: LastFmRepositoryProtocol | None = None,
    ) -> None:
        self._mb_repo = musicbrainz_repo
        self._lb_repo = listenbrainz_repo
        self._preferences = preferences_service
        self._integration = integration
        self._memory_cache = memory_cache
        self._wikidata_repo = wikidata_repo
        self._lfm_repo = lastfm_repo
        self._enrich_in_flight: dict[str, asyncio.Future[DiscoverQueueEnrichment]] = {}

    async def enrich_queue_item(self, release_group_mbid: str) -> DiscoverQueueEnrichment:
        cache_key = f"{DISCOVER_QUEUE_ENRICH_PREFIX}{release_group_mbid}"
        if self._memory_cache:
            cached = await self._memory_cache.get(cache_key)
            if cached is not None and isinstance(cached, DiscoverQueueEnrichment):
                return cached

        if release_group_mbid in self._enrich_in_flight:
            return await asyncio.shield(self._enrich_in_flight[release_group_mbid])

        loop = asyncio.get_running_loop()
        future: asyncio.Future[DiscoverQueueEnrichment] = loop.create_future()
        self._enrich_in_flight[release_group_mbid] = future
        try:
            result = await self._do_enrich_queue_item(release_group_mbid, cache_key)
            if not future.done():
                future.set_result(result)
            return result
        except BaseException as exc:
            if not future.done():
                future.set_exception(exc)
            raise
        finally:
            self._enrich_in_flight.pop(release_group_mbid, None)

    async def _do_enrich_queue_item(
        self, release_group_mbid: str, cache_key: str
    ) -> DiscoverQueueEnrichment:

        enrichment = DiscoverQueueEnrichment()

        rg_data = await self._mb_repo.get_release_group_by_id(
            release_group_mbid,
            includes=["artist-credits", "releases", "tags", "url-rels"],
        )

        artist_mbid = ""
        youtube_url = None

        if rg_data:
            tags_raw = rg_data.get("tags", [])
            enrichment.tags = [t.get("name", "") for t in tags_raw if t.get("name")][:10]

            youtube_raw = self._mb_repo.extract_youtube_url_from_relations(rg_data)
            if youtube_raw:
                youtube_url = self._mb_repo.youtube_url_to_embed(youtube_raw)

            ac_list = rg_data.get("artist-credit", [])
            for ac in ac_list:
                a = ac.get("artist", {}) if isinstance(ac, dict) else {}
                if a.get("id"):
                    artist_mbid = a["id"]
                    break
            enrichment.artist_mbid = artist_mbid or None

            releases = rg_data.get("releases") or rg_data.get("release-list", [])
            if releases:
                first_release = releases[0]
                enrichment.release_date = first_release.get("date")

                if not youtube_url:
                    release_data = await self._mb_repo.get_release_by_id(
                        first_release["id"],
                        includes=["recordings", "url-rels"],
                    )
                    if release_data:
                        yt_raw = self._mb_repo.extract_youtube_url_from_relations(release_data)
                        if yt_raw:
                            youtube_url = self._mb_repo.youtube_url_to_embed(yt_raw)

                        if not youtube_url:
                            tracks = release_data.get("media") or release_data.get("medium-list", [])
                            rec_ids: list[str] = []
                            for medium in tracks:
                                for track in medium.get("tracks") or medium.get("track-list", []):
                                    rec_id = track.get("recording", {}).get("id")
                                    if rec_id:
                                        rec_ids.append(rec_id)
                                    if len(rec_ids) >= 3:
                                        break
                                if len(rec_ids) >= 3:
                                    break
                            if rec_ids:
                                rec_results = await asyncio.gather(
                                    *[
                                        self._mb_repo.get_recording_by_id(rid, includes=["url-rels"])
                                        for rid in rec_ids
                                    ],
                                    return_exceptions=True,
                                )
                                for rec_data in rec_results:
                                    if isinstance(rec_data, Exception) or not rec_data:
                                        continue
                                    yt_raw = self._mb_repo.extract_youtube_url_from_relations(rec_data)
                                    if yt_raw:
                                        youtube_url = self._mb_repo.youtube_url_to_embed(yt_raw)
                                        break

        enrichment.youtube_url = youtube_url

        if not youtube_url:
            yt_settings = self._preferences.get_youtube_connection()
            enrichment.youtube_search_available = yt_settings.enabled and yt_settings.api_enabled and yt_settings.has_valid_api_key()

        album_name = rg_data.get("title", "") if rg_data else ""
        artist_name_for_search = ""
        if rg_data:
            ac_list = rg_data.get("artist-credit", [])
            for ac in ac_list:
                a = ac.get("artist", {}) if isinstance(ac, dict) else {}
                if a.get("name"):
                    artist_name_for_search = a["name"]
                    break
        enrichment.youtube_search_url = (
            f"https://www.youtube.com/results?search_query={quote_plus(f'{artist_name_for_search} {album_name}')}"
        )

        async def _get_artist_and_bio():
            if not artist_mbid:
                return
            try:
                mb_artist = await self._mb_repo.get_artist_by_id(artist_mbid)
                if mb_artist:
                    enrichment.country = mb_artist.get("country") or mb_artist.get("area", {}).get("name", "")
                    if self._wikidata_repo:
                        url_rels = mb_artist.get("relations", [])
                        wiki_url = None
                        for rel in url_rels:
                            if rel.get("type") in ("wikipedia", "wikidata"):
                                url_obj = rel.get("url", {})
                                wiki_url = url_obj.get("resource", "") if isinstance(url_obj, dict) else ""
                                break
                        if wiki_url:
                            bio = await self._wikidata_repo.get_wikipedia_extract(wiki_url)
                            if bio:
                                enrichment.artist_description = bio
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Failed to get artist MB data: {e}")

        async def _get_listen_count():
            try:
                counts = await self._lb_repo.get_release_group_popularity_batch(
                    [release_group_mbid]
                )
                if counts:
                    enrichment.listen_count = counts.get(release_group_mbid)
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Failed to get listen count: {e}")

        async def _apply_lastfm_fallback():
            if not self._lfm_repo or not self._integration.is_lastfm_enabled():
                return
            if not album_name or not artist_name_for_search:
                return

            try:
                album_info = await self._lfm_repo.get_album_info(
                    artist=artist_name_for_search,
                    album=album_name,
                )
                if album_info:
                    if not enrichment.tags and album_info.tags:
                        enrichment.tags = [tag.name for tag in album_info.tags if tag.name][:10]
                    if not enrichment.artist_description and album_info.summary:
                        cleaned_summary = clean_lastfm_bio(album_info.summary)
                        if cleaned_summary:
                            enrichment.artist_description = cleaned_summary
            except Exception as e:  # noqa: BLE001
                logger.debug("Failed Last.fm album fallback for discover queue: %s", e)

            if enrichment.artist_description and enrichment.tags:
                return

            try:
                artist_info = await self._lfm_repo.get_artist_info(
                    artist=artist_name_for_search,
                    mbid=artist_mbid or None,
                )
                if not artist_info:
                    return
                if not enrichment.artist_mbid and artist_info.mbid:
                    enrichment.artist_mbid = artist_info.mbid
                if not enrichment.tags and artist_info.tags:
                    enrichment.tags = [tag.name for tag in artist_info.tags if tag.name][:10]
                if not enrichment.artist_description and artist_info.bio_summary:
                    cleaned_bio = clean_lastfm_bio(artist_info.bio_summary)
                    if cleaned_bio:
                        enrichment.artist_description = cleaned_bio
            except Exception as e:  # noqa: BLE001
                logger.debug("Failed Last.fm artist fallback for discover queue: %s", e)

        await asyncio.gather(_get_artist_and_bio(), _get_listen_count(), _apply_lastfm_fallback())

        if self._memory_cache:
            enrich_ttl = self._integration.get_queue_settings().enrich_ttl
            await self._memory_cache.set(cache_key, enrichment, enrich_ttl)

        return enrichment
