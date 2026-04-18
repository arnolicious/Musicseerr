<script lang="ts">
	import {
		getUpdateCheckQuery,
		getVersionQuery,
		getReleaseHistoryQuery
	} from '$lib/queries/VersionQuery.svelte';
	import UpdateBanner from '$lib/components/UpdateBanner.svelte';
	import WhatsNewModal from '$lib/components/WhatsNewModal.svelte';

	let { updateAvailable = $bindable(false) }: { updateAvailable: boolean } = $props();

	const updateCheckQuery = getUpdateCheckQuery();
	const versionQuery = getVersionQuery();
	const releaseHistoryQuery = getReleaseHistoryQuery();

	const currentVersion = $derived(versionQuery.data?.version ?? null);
	const buildDate = $derived(versionQuery.data?.build_date ?? null);
	const isDev = $derived(currentVersion === 'dev' || currentVersion === 'hosting-local');

	function getMinorPrefix(tag: string): string | null {
		const m = tag.replace(/^v/, '').match(/^(\d+\.\d+)\./);
		return m ? m[1] : null;
	}

	// Collect all releases sharing the same minor version (e.g. v1.3.0, v1.3.1, …)
	const minorReleases = $derived.by(() => {
		const releases = releaseHistoryQuery.data;
		if (!releases || releases.length === 0) return [];

		const versionToMatch = isDev ? releases[0].tag_name : currentVersion;
		if (!versionToMatch) return [];

		const prefix = getMinorPrefix(versionToMatch);
		if (!prefix) {
			const exact = releases.find((r) => r.tag_name === versionToMatch);
			return exact ? [exact] : [];
		}

		return releases.filter((r) => getMinorPrefix(r.tag_name) === prefix);
	});

	$effect(() => {
		updateAvailable = updateCheckQuery.data?.update_available ?? false;
	});
</script>

<UpdateBanner
	updateAvailable={updateCheckQuery.data?.update_available ?? false}
	latestVersion={updateCheckQuery.data?.latest_version ?? null}
/>
<WhatsNewModal {currentVersion} {buildDate} releases={minorReleases} />
