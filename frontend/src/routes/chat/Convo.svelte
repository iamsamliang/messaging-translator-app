<script lang="ts">
	import { latestMessages } from '$lib/stores/stores';
	import { createEventDispatcher, type EventDispatcher } from 'svelte';

	export let chatName: string;
	export let isSelected: boolean;
	export let convoID: number;
	export let isGroupChat: boolean;
	export let url: string | null;
	export let itemHeight: number;

	const dispatch: EventDispatcher<any> = createEventDispatcher();

	function handleClick(): void {
		dispatch('click');
	}
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<li
	class="chat hover:bg-neutral-800 cursor-pointer rounded-lg py-2 px-3"
	style="height: {itemHeight}px;"
	class:is-selected={isSelected}
	id={convoID.toString()}
	on:click={handleClick}
	aria-label={`Select conversation with ${chatName}`}
>
	<div class="flex-shrink-0 w-fit h-[80%] overflow-hidden min-[1047px]:mr-[15px]">
		{#if url}
			<img
				src={url}
				alt="The conversation's profile"
				class="min-w-full h-full overflow-hidden rounded-full"
			/>
		{:else if isGroupChat}
			<!-- Group Chat Icon -->
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="1"
				stroke="currentColor"
				class="h-full text-neutral-200"
				class:text-gray-200={isSelected}
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z"
				/>
			</svg>
		{:else}
			<!-- Non-group Chat Icon -->
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="1.1"
				stroke="currentColor"
				class="h-full text-neutral-200"
				class:text-gray-200={isSelected}
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
				/>
			</svg>
		{/if}
	</div>
	<div
		class="h-[90%] flex-col justify-start text-[1.06rem] gap-[2px] flex-1 min-w-0 mr-[5px] hidden min-[1047px]:flex"
	>
		<div
			class="text-base font-semibold overflow-hidden text-ellipsis text-neutral-200"
			class:is-selected-color={isSelected}
		>
			{chatName}
		</div>

		<div
			class="text-[0.9rem] text-neutral-500 overflow-hidden text-ellipsis truncate"
			class:is-selected-color={isSelected}
		>
			{#if $latestMessages[convoID]}
				{$latestMessages[convoID].text}
			{/if}
		</div>
	</div>
	<div
		class="flex-grow-0 flex-shrink-0 basis-auto flex-col gap-[0.8rem] items-end h-full hidden min-[1047px]:flex"
	>
		<div class="text-neutral-500 text-[0.9rem]" class:is-selected-color={isSelected}>
			{#if $latestMessages[convoID]}
				{$latestMessages[convoID].time}
			{/if}
		</div>
		<div
			class="bg-[#007bff] text-white rounded-full flex items-center justify-center w-[0.6rem] h-[0.6rem]"
			class:hidden={$latestMessages[convoID] ? $latestMessages[convoID].isRead : true}
		></div>
	</div>
</li>

<style>
	/* Style each chat item */
	.chat {
		display: flex;
		align-items: center;
		border-bottom: 1px solid none;
		/* height: 80px; */
		/* Separator between chats */
	}

	.is-selected {
		background-color: #0059ffeb;
	}

	.is-selected-color {
		color: white;
	}
</style>
