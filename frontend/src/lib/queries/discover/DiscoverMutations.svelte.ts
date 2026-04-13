import { api } from '$lib/api/client';
import { API } from '$lib/constants';
import { createMutation } from '@tanstack/svelte-query';
import { queryClient } from '../QueryClient';
import { DiscoverQueryKeyFactory } from './DiscoverQueryKeyFactory';

export const createDiscoverRefreshMutation = () =>
	createMutation(() => ({
		mutationFn: () => api.global.post(API.discoverRefresh()),
		onSuccess: () => {
			queryClient.invalidateQueries({
				queryKey: DiscoverQueryKeyFactory.prefix
			});
		}
	}));
