export type PlaybackState =
	| 'idle'
	| 'loading'
	| 'playing'
	| 'paused'
	| 'ended'
	| 'buffering'
	| 'error';

export type SourceType = 'youtube' | 'local' | 'jellyfin' | 'navidrome';

export type QueueOrigin = 'context' | 'manual';

export interface PlaybackSource {
	readonly type: SourceType;

	load(info: {
		trackSourceId?: string;
		url?: string;
		token?: string;
		format?: string;
		duration?: number;
	}): Promise<void>;
	play(): void;
	pause(): void;
	seekTo(seconds: number): void;
	setVolume(level: number): void;
	getCurrentTime(): number;
	getDuration(): number;
	isSeekable?(): boolean;
	destroy(): void;

	onStateChange(callback: (state: PlaybackState) => void): void;
	onReady(callback: () => void): void;
	onError(callback: (error: { code: string; message: string }) => void): void;
	onProgress(callback: (currentTime: number, duration: number) => void): void;
}

export interface NowPlaying {
	albumId: string;
	albumName: string;
	artistName: string;
	coverUrl: string | null;
	sourceType: SourceType;
	discNumber?: number;
	trackSourceId?: string;
	embedUrl?: string;
	trackName?: string;
	artistId?: string;
	streamUrl?: string;
	format?: string;
	playlistTrackId?: string;
}

export type PlaybackMeta = {
	albumId: string;
	albumName: string;
	artistName: string;
	coverUrl: string | null;
	artistId?: string;
};

export interface QueueItem {
	/** Source-specific item identifier (Jellyfin item ID / local file ID / YouTube video ID) */
	trackSourceId: string;
	trackName: string;
	artistName: string;
	trackNumber: number;
	discNumber?: number;
	albumId: string;
	albumName: string;
	coverUrl: string | null;
	sourceType: SourceType;
	artistId?: string;
	streamUrl?: string;
	format?: string;
	availableSources?: SourceType[];
	sourceIds?: Partial<Record<SourceType, string>>;
	duration?: number;
	playSessionId?: string;
	queueOrigin?: QueueOrigin;
	/** Stable playlist-level track identifier — survives source changes */
	playlistTrackId?: string;
}
