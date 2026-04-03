import { browser } from '$app/environment';
import { api } from '$lib/api/client';

const POLL_INTERVAL_MS = 10_000;

function createRequestCountStore() {
	let count = $state(0);
	let pageActive = $state(false);
	let pollInterval: ReturnType<typeof setInterval> | null = null;

	async function poll(): Promise<void> {
		try {
			const data = await api.global.get<{ count?: number }>('/api/v1/requests/active/count');
			count = data.count ?? 0;
		} catch {
			// ignore polling errors
		}
	}

	function clearPoll(): void {
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}
	}

	function startPolling(): void {
		if (!browser) return;
		void poll();
		clearPoll();
		pollInterval = setInterval(() => void poll(), POLL_INTERVAL_MS);
	}

	function stopPolling(): void {
		clearPoll();
	}

	function setPageActive(active: boolean): void {
		pageActive = active;
		if (active) {
			clearPoll();
		} else {
			startPolling();
		}
	}

	function notify(newCount?: number): void {
		if (typeof newCount === 'number') {
			count = newCount;
			return;
		}
		void poll();
	}

	return {
		get count() {
			return count;
		},
		get isPageActive() {
			return pageActive;
		},
		startPolling,
		stopPolling,
		setPageActive,
		notify
	};
}

export const requestCountStore = createRequestCountStore();
