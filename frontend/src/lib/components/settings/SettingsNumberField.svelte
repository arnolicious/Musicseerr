<script lang="ts">
	let {
		label,
		description,
		value = $bindable(0),
		min = 0,
		max = 999999,
		step = 1,
		unit = ''
	}: {
		label: string;
		description: string;
		value: number;
		min?: number;
		max?: number;
		step?: number;
		unit?: string;
	} = $props();
</script>

<fieldset class="fieldset">
	<legend class="fieldset-legend">{label}</legend>
	<label class="input w-full">
		<input type="number" bind:value {min} {max} {step} class="grow" />
		{#if unit}
			<span class="label">{unit}</span>
		{/if}
	</label>
	<p class="label text-base-content/50">{description}</p>
</fieldset>
