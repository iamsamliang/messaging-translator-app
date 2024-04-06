<script lang="ts">
	import { observeLast } from '$lib/actions/intersectionObserver';
	import { createEventDispatcher } from 'svelte';

	export let items: any[];
	export let loadedAll: boolean;
	export let root: HTMLElement;
	export let rootMargin: string;

	const dispatch = createEventDispatcher();
</script>

{#each items as item, index}
	{#if !loadedAll && index === 0}
		<div
			on:intersecting={() => dispatch('loadMore')}
			use:observeLast={{ root, rootMargin }}
			class="flex flex-col gap-1"
		>
			<slot {item} />
		</div>
	{:else}
		<slot {item} />
	{/if}
{/each}
