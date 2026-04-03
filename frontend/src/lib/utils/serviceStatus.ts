import { serviceStatusStore } from '$lib/stores/serviceStatus';

/**
 * Extract and record `service_status` from a parsed JSON response body.
 * Call this after parsing JSON from any API response that may include
 * the optional `service_status` field.
 */
export function extractServiceStatus(data: unknown): void {
	if (data && typeof data === 'object' && 'service_status' in data) {
		const status = (data as Record<string, unknown>).service_status;
		if (status && typeof status === 'object' && !Array.isArray(status)) {
			serviceStatusStore.recordFromResponse(status as Record<string, string>);
		}
	}
}
