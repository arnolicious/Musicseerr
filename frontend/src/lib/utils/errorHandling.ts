import { isValidMbid } from '$lib/utils/formatting';

export function isAbortError(error: unknown): boolean {
	return (
		(error instanceof DOMException && error.name === 'AbortError') ||
		(error instanceof Error && error.name === 'AbortError')
	);
}

export function getCoverUrl(coverUrl: string | null | undefined, albumId: string): string {
	if (isValidMbid(albumId)) {
		return `/api/v1/covers/release-group/${albumId}?size=250`;
	}
	return coverUrl || `/api/v1/covers/release-group/${albumId}?size=250`;
}
