"""Pre-cache orchestrator — delegates to phase sub-services."""

from __future__ import annotations

import logging
import asyncio
from typing import Any, TYPE_CHECKING

from repositories.protocols import LidarrRepositoryProtocol, CoverArtRepositoryProtocol
from repositories.coverart_disk_cache import get_cache_filename
from services.cache_status_service import CacheStatusService
from core.exceptions import ExternalServiceError
from infrastructure.cache.cache_keys import ALBUM_INFO_PREFIX
from infrastructure.validators import is_unknown_mbid

from .artist_phase import ArtistPhase
from .album_phase import AlbumPhase
from .audiodb_phase import AudioDBPhase

if TYPE_CHECKING:
    from infrastructure.persistence import SyncStateStore, GenreIndex, LibraryDB
    from services.audiodb_image_service import AudioDBImageService

logger = logging.getLogger(__name__)


class LibraryPrecacheService:
    def __init__(
        self,
        lidarr_repo: LidarrRepositoryProtocol,
        cover_repo: CoverArtRepositoryProtocol,
        preferences_service: Any,
        sync_state_store: "SyncStateStore",
        genre_index: "GenreIndex",
        library_db: "LibraryDB",
        artist_discovery_service: Any = None,
        audiodb_image_service: 'AudioDBImageService | None' = None,
    ):
        self._lidarr_repo = lidarr_repo
        self._cover_repo = cover_repo
        self._preferences_service = preferences_service
        self._sync_state_store = sync_state_store
        self._artist_discovery_service = artist_discovery_service
        self._audiodb_image_service = audiodb_image_service

        self._artist_phase = ArtistPhase(lidarr_repo, cover_repo, preferences_service, genre_index, sync_state_store)
        self._album_phase = AlbumPhase(cover_repo, preferences_service, sync_state_store)
        self._audiodb_phase = AudioDBPhase(cover_repo, preferences_service, audiodb_image_service)

    # Delegation for backward compat (tests access private methods)
    async def _check_audiodb_cache_needs(self, artists, albums):
        return await self._audiodb_phase.check_cache_needs(artists, albums)

    async def _precache_audiodb_data(self, artists, albums, status_service):
        return await self._audiodb_phase.precache_audiodb_data(artists, albums, status_service)

    async def _download_audiodb_bytes(self, url, entity_type, mbid):
        return await self._audiodb_phase.download_bytes(url, entity_type, mbid)

    def _sort_by_cover_priority(self, items, item_type):
        return self._audiodb_phase.sort_by_cover_priority(items, item_type)

    async def precache_library_resources(self, artists: list[dict], albums: list[Any], resume: bool = False) -> None:
        status_service = CacheStatusService(self._sync_state_store)
        task = None
        try:
            task = asyncio.create_task(self._do_precache(artists, albums, status_service, resume))
            from core.task_registry import TaskRegistry
            TaskRegistry.get_instance().register("precache-library", task)
            await asyncio.wait_for(task, timeout=1800.0)
        except asyncio.TimeoutError:
            logger.error("Library pre-cache operation timed out after 30 minutes")
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info("Pre-cache task successfully cancelled after timeout")
                except Exception as e:  # noqa: BLE001
                    logger.error(f"Error during task cancellation: {e}")
            await status_service.complete_sync("Sync timed out after 30 minutes")
            raise ExternalServiceError("Library sync timed out - too many items or slow network")
        except asyncio.CancelledError:
            logger.warning("Pre-cache was cancelled")
            await status_service.complete_sync()
            raise
        except Exception as e:
            logger.error(f"Pre-cache failed: {e}")
            await status_service.complete_sync(str(e))
            raise

    async def _do_precache(self, artists: list[dict], albums: list[Any], status_service: CacheStatusService, resume: bool = False) -> None:
        from core.dependencies import get_album_service
        try:
            processed_artists: set[str] = set()
            processed_albums: set[str] = set()
            skip_artists = False

            if resume:
                logger.info("Resuming interrupted sync...")
                processed_artists = await self._sync_state_store.get_processed_items('artist')
                processed_albums = await self._sync_state_store.get_processed_items('album')

                state = await self._sync_state_store.get_sync_state()
                if state and state.get('phase') == 'albums':
                    skip_artists = True
                    logger.info(f"Resuming from albums phase, {len(processed_albums)} albums already processed")
                else:
                    logger.info(f"Resuming from artists phase, {len(processed_artists)} artists already processed")

            total_artists = len(artists)
            total_albums = len(albums)

            logger.info(f"Starting pre-cache for {total_artists} monitored artists and {total_albums} monitored albums")
            logger.info("Pre-fetching Lidarr library data...")
            album_service = get_album_service()
            library_artist_mbids = await self._lidarr_repo.get_artist_mbids()
            library_album_mbids = await self._lidarr_repo.get_library_mbids(include_release_ids=True)
            logger.info(f"Lidarr data cached: {len(library_artist_mbids)} artists, {len(library_album_mbids)} albums")

            if not skip_artists:
                remaining_artists = [a for a in artists if a.get('mbid') not in processed_artists]
                logger.info(f"Phase 1: Caching {len(remaining_artists)} artist metadata + images ({len(processed_artists)} already done)")
                if remaining_artists:
                    await status_service.start_sync('artists', len(remaining_artists), total_artists=total_artists, total_albums=total_albums)
                    await self._artist_phase.precache_artist_images(remaining_artists, status_service, library_artist_mbids, library_album_mbids, len(processed_artists))
                else:
                    await status_service.start_sync('artists', 0, total_artists=total_artists, total_albums=total_albums)
                    await status_service.skip_phase('artists')
            if status_service.is_cancelled():
                logger.info("Pre-cache cancelled after Phase 1")
                return

            if self._artist_discovery_service and not skip_artists:
                artist_mbids = [
                    a.get('mbid') for a in artists
                    if a.get('mbid') and not a.get('mbid', '').startswith('unknown_')
                ]
                if artist_mbids:
                    logger.info(f"Phase 1.5: Pre-caching discovery data (popular albums/songs/similar) for {len(artist_mbids)} library artists")
                    await status_service.update_phase('discovery', len(artist_mbids))
                    mbid_to_name = {
                        a.get('mbid'): a.get('name', a.get('mbid', '')[:8])
                        for a in artists if a.get('mbid')
                    }
                    try:
                        advanced_settings = self._preferences_service.get_advanced_settings()
                        precache_delay = advanced_settings.artist_discovery_precache_delay
                        await self._artist_discovery_service.precache_artist_discovery(
                            artist_mbids, delay=precache_delay,
                            status_service=status_service, mbid_to_name=mbid_to_name,
                        )
                    except Exception as e:  # noqa: BLE001
                        logger.warning(f"Discovery precache failed (non-fatal): {e}")
                else:
                    await status_service.skip_phase('discovery')
            elif not skip_artists:
                await status_service.skip_phase('discovery')

            if status_service.is_cancelled():
                logger.info("Pre-cache cancelled after Phase 1.5")
                return

            monitored_mbids: set[str] = set()
            for a in albums:
                mbid = getattr(a, 'musicbrainz_id', None) if hasattr(a, 'musicbrainz_id') else a.get('mbid') if isinstance(a, dict) else None
                if not is_unknown_mbid(mbid):
                    monitored_mbids.add(mbid.lower())
            logger.info(f"Phase 2: Collecting {len(monitored_mbids)} monitored album MBIDs (unmonitored albums will NOT be pre-cached)")
            deduped_release_groups = list(monitored_mbids)
            if status_service.is_cancelled():
                logger.info("Pre-cache cancelled after Phase 2")
                return
            logger.info(f"Phase 3: Batch-checking which of {len(deduped_release_groups)} release-groups need caching...")
            items_needing_metadata = []
            cache_checks = []
            for rgid in deduped_release_groups:
                if rgid in processed_albums:
                    continue
                cache_key = f"{ALBUM_INFO_PREFIX}{rgid}"
                cache_checks.append((rgid, album_service._cache.get(cache_key)))
            cache_results = await asyncio.gather(*[check for _, check in cache_checks])
            for (rgid, _), cached_info in zip(cache_checks, cache_results):
                if not cached_info:
                    items_needing_metadata.append(rgid)
            items_needing_covers = []
            cover_paths = []
            for rgid in deduped_release_groups:
                if rgid in processed_albums:
                    continue
                if rgid.lower() in monitored_mbids:
                    cache_filename = get_cache_filename(f"rg_{rgid}", "500")
                    file_path = self._cover_repo.cache_dir / f"{cache_filename}.bin"
                    cover_paths.append((rgid, file_path))
            for rgid, file_path in cover_paths:
                if not file_path.exists():
                    items_needing_covers.append(rgid)
            items_to_process = list(set(items_needing_metadata + items_needing_covers))
            already_cached = len(deduped_release_groups) - len(items_to_process) - len(processed_albums)
            logger.info(
                f"Phase 3: {len(items_to_process)} items need caching "
                f"({len(items_needing_metadata)} metadata, {len(items_needing_covers)} covers) - "
                f"{already_cached} already cached, {len(processed_albums)} from previous run"
            )
            if items_to_process:
                await status_service.update_phase('albums', len(items_to_process))
                await self._album_phase.precache_album_data(items_to_process, monitored_mbids, status_service, library_album_mbids, len(processed_albums))
            else:
                await status_service.skip_phase('albums')

            if not status_service.is_cancelled():
                try:
                    await self._audiodb_phase.precache_audiodb_data(artists, albums, status_service)
                except Exception as e:  # noqa: BLE001
                    logger.error(f"AudioDB pre-warming failed (non-fatal): {e}")

            logger.info("Library resource pre-caching complete")
        except Exception as e:
            logger.error(f"Error during pre-cache: {e}")
            raise
        finally:
            if status_service.is_syncing():
                await status_service.complete_sync()
