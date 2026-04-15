import { playerStore } from '$lib/stores/player.svelte';
import { buildQueueItemsFromYouTube, type TrackMeta } from '$lib/player/queueHelpers';
import type { YouTubeTrackLink } from '$lib/types';
import { getCoverUrl } from '$lib/utils/errorHandling';

type TrackQueueOptions = {
	albumId: string;
	albumName: string;
	artistName: string;
	coverUrl: string | null;
	artistId?: string;
};

export function launchTrackPlayback(
	trackLinks: YouTubeTrackLink[],
	startIndex: number = 0,
	shuffle: boolean = false,
	options: TrackQueueOptions
): void {
	const meta: TrackMeta = {
		albumId: options.albumId,
		albumName: options.albumName,
		artistName: options.artistName,
		coverUrl: getCoverUrl(options.coverUrl, options.albumId),
		artistId: options.artistId
	};

	const items = buildQueueItemsFromYouTube(trackLinks, meta);
	playerStore.playQueue(items, startIndex, shuffle);
}
