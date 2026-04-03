import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

vi.mock('$app/environment', () => ({ browser: true }));
vi.mock('$lib/api/client', () => ({
	api: {
		global: {
			get: vi.fn().mockResolvedValue({ count: 0 })
		}
	}
}));

import { requestCountStore } from './requestCountStore.svelte';
import { api } from '$lib/api/client';

const mockGet = vi.mocked(api.global.get);

describe('requestCountStore', () => {
	beforeEach(() => {
		vi.useFakeTimers();
		requestCountStore.stopPolling();
		requestCountStore.notify(0);
		mockGet.mockResolvedValue({ count: 0 });
	});

	afterEach(() => {
		requestCountStore.stopPolling();
		vi.useRealTimers();
	});

	it('starts with count 0', () => {
		expect.assertions(1);
		expect(requestCountStore.count).toBe(0);
	});

	it('notify with count sets count directly', () => {
		expect.assertions(1);
		requestCountStore.notify(5);
		expect(requestCountStore.count).toBe(5);
	});

	it('notify without count triggers a poll', async () => {
		expect.assertions(1);
		mockGet.mockResolvedValue({ count: 3 });
		requestCountStore.notify();
		await vi.runAllTimersAsync();
		expect(requestCountStore.count).toBe(3);
	});

	it('startPolling fetches immediately and sets interval', async () => {
		expect.assertions(2);
		mockGet.mockResolvedValue({ count: 7 });
		requestCountStore.startPolling();
		await vi.advanceTimersByTimeAsync(0);
		expect(requestCountStore.count).toBe(7);
		expect(mockGet).toHaveBeenCalledWith('/api/v1/requests/active/count');
	});

	it('stopPolling clears the interval', async () => {
		expect.assertions(1);
		requestCountStore.startPolling();
		await vi.advanceTimersByTimeAsync(0);
		mockGet.mockClear();
		requestCountStore.stopPolling();
		await vi.advanceTimersByTimeAsync(20_000);
		expect(mockGet).not.toHaveBeenCalled();
	});

	it('setPageActive(true) pauses polling', async () => {
		expect.assertions(1);
		requestCountStore.startPolling();
		await vi.advanceTimersByTimeAsync(0);
		mockGet.mockClear();
		requestCountStore.setPageActive(true);
		await vi.advanceTimersByTimeAsync(20_000);
		expect(mockGet).not.toHaveBeenCalled();
	});

	it('setPageActive(false) resumes polling', async () => {
		expect.assertions(1);
		requestCountStore.setPageActive(true);
		mockGet.mockClear();
		mockGet.mockResolvedValue({ count: 2 });
		requestCountStore.setPageActive(false);
		await vi.advanceTimersByTimeAsync(10_000);
		expect(mockGet).toHaveBeenCalled();
	});

	it('isPageActive reflects current state', () => {
		expect.assertions(2);
		requestCountStore.setPageActive(true);
		expect(requestCountStore.isPageActive).toBe(true);
		requestCountStore.setPageActive(false);
		expect(requestCountStore.isPageActive).toBe(false);
	});

	it('handles poll errors gracefully', async () => {
		expect.assertions(1);
		requestCountStore.notify(5);
		mockGet.mockRejectedValue(new Error('network'));
		requestCountStore.startPolling();
		await vi.advanceTimersByTimeAsync(0);
		expect(requestCountStore.count).toBe(5);
	});
});
