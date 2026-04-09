import { api } from '$lib/api/client';
import { DEFAULT_SOURCE, isMusicSource } from '$lib/stores/musicSource';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async () => {
	const data = await api.global.get<{ source: unknown }>('/api/v1/settings/primary-source');
	const primarySource = isMusicSource(data.source) ? data.source : DEFAULT_SOURCE;

	return {
		primarySource
	};
};
