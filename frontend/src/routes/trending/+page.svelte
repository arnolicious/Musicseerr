<script lang="ts">
	import TimeRangeView from '$lib/components/TimeRangeView.svelte';
	import SourceSwitcher from '$lib/components/SourceSwitcher.svelte';
	import { type MusicSource } from '$lib/stores/musicSource';
	import { Mic } from 'lucide-svelte';
	import { PersistedState } from 'runed';
	import { PAGE_SOURCE_KEYS } from '$lib/constants';
	import type { PageProps } from './$types';

	const { data }: PageProps = $props();

	// svelte-ignore state_referenced_locally
	let activeSource = new PersistedState<MusicSource>(
		PAGE_SOURCE_KEYS['trending'],
		data.primarySource
	);

	function handleSourceChange(nextSource: MusicSource) {
		activeSource.current = nextSource;
	}

	let sourceLabel = $derived(activeSource.current === 'lastfm' ? 'Last.fm' : 'ListenBrainz');
</script>

<svelte:head>
	<title>Trending Artists - Musicseerr</title>
</svelte:head>

<div class="space-y-4 px-4 sm:px-6 lg:px-8">
	<div class="flex justify-end">
		<SourceSwitcher pageKey="trending" onSourceChange={handleSourceChange} />
	</div>
	<TimeRangeView
		itemType="artist"
		endpoint="/api/v1/home/trending/artists"
		title="Trending Artists"
		subtitle={`Most listened artists on ${sourceLabel}`}
		source={activeSource.current}
		errorIcon={Mic}
	/>
</div>
