import { ArtistQueryKeyFactory } from '$lib/queries/artist/ArtistQueryKeyFactory';
import { queryClient } from '$lib/queries/QueryClient';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
	console.log('Prefetching artist data for artist ID:', params.id);
	queryClient.prefetchQuery({
		queryKey: ArtistQueryKeyFactory.basic(params.id)
	});

	return {
		artistId: params.id
	};
};
