import { libraryStore } from '$lib/stores/library';
import { API } from '$lib/constants';
import { api } from '$lib/api/client';

export interface AlbumRemoveResult {
	success: boolean;
	artist_removed: boolean;
	artist_name?: string | null;
	error?: string;
}

export interface AlbumRemovePreviewResult {
	success: boolean;
	artist_will_be_removed: boolean;
	artist_name?: string | null;
	error?: string;
}

export async function getAlbumRemovePreview(
	musicbrainzId: string
): Promise<AlbumRemovePreviewResult> {
	try {
		const data = await api.global.get<{
			artist_will_be_removed?: boolean;
			artist_name?: string | null;
		}>(API.library.removeAlbumPreview(musicbrainzId));
		return {
			success: true,
			artist_will_be_removed: data.artist_will_be_removed ?? false,
			artist_name: data.artist_name ?? null
		};
	} catch (e) {
		return {
			success: false,
			artist_will_be_removed: false,
			error: e instanceof Error ? e.message : 'Unknown error'
		};
	}
}

export async function removeAlbum(
	musicbrainzId: string,
	deleteFiles: boolean = false
): Promise<AlbumRemoveResult> {
	try {
		const url = `${API.library.removeAlbum(musicbrainzId)}?delete_files=${deleteFiles}`;
		const data = await api.global.delete<{
			artist_removed?: boolean;
			artist_name?: string | null;
		}>(url);
		libraryStore.removeMbid(musicbrainzId);
		return {
			success: true,
			artist_removed: data?.artist_removed ?? false,
			artist_name: data?.artist_name ?? null
		};
	} catch (e) {
		return {
			success: false,
			artist_removed: false,
			error: e instanceof Error ? e.message : 'Unknown error'
		};
	}
}
