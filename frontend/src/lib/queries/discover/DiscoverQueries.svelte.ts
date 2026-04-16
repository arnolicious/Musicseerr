import { api } from '$lib/api/client';
import { API, CACHE_TTL } from '$lib/constants';
import type { MusicSource } from '$lib/stores/musicSource';
import type { DiscoverResponse } from '$lib/types';
import { createQuery } from '@tanstack/svelte-query';
import { DiscoverQueryKeyFactory } from './DiscoverQueryKeyFactory';
import type { Getter } from 'runed';

const RETRY_INTERVAL = 3_000; // 3 seconds
const RETRY_COUNT = 80; // 80 retries at 3 seconds each equals 4 minutes
// const RETRY_COUNT_TEST = 3;

class EmptyDataError extends Error {
	constructor(message: string) {
		super(message);
		this.name = 'EmptyDataError';
	}
}

export const getDiscoverQuery = (getSource: Getter<MusicSource>) => {
	return createQuery(() => ({
		staleTime: CACHE_TTL.DISCOVER,
		queryKey: DiscoverQueryKeyFactory.discover(getSource()),
		retry: (failureCount, error) => {
			// Retry if the error is due to empty data
			if (error instanceof EmptyDataError && failureCount < RETRY_COUNT) {
				console.debug(
					`Discover query attempt ${failureCount}: ${error.message}. Retrying in ${RETRY_INTERVAL / 1000} seconds...`
				);
				return true; // Retry the query
			}
			return false; // Do not retry for other types of errors
		},

		queryFn: async ({ signal }) => {
			const result = await api.global.get<DiscoverResponse>(API.discover(getSource()), {
				signal
			});

			const dataHasContent =
				(result?.because_you_listen_to?.length ?? 0) > 0 ||
				result?.fresh_releases != null ||
				result?.missing_essentials != null ||
				result?.globally_trending != null;
			console.debug('Discover query data has content:', dataHasContent, result);
			if (!dataHasContent) {
				// Throw error to trigger retry mechanism in case of empty data
				throw new EmptyDataError('Discover query returned empty data');
			}

			return result;
		}
	}));
};

export type DiscoverQuery = ReturnType<typeof getDiscoverQuery>;
