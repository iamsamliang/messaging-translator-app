<script lang="ts">
	import { latestMessages } from '$lib/stores/stores';
	import { createEventDispatcher, type EventDispatcher } from 'svelte';

	export let chatName: string;
	export let isSelected: boolean;
	export let convoID: number;

	const dispatch: EventDispatcher<any> = createEventDispatcher();

	function handleClick(): void {
		dispatch('click');
	}
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<li
	class="chat hover:bg-gray-300 cursor-pointer rounded-lg"
	class:is-selected={isSelected}
	id={convoID.toString()}
	on:click={handleClick}
	aria-label={`Select conversation with ${chatName}`}
>
	<div
		class="flex-grow-0 flex-shrink-0 basis-auto h-[75%] rounded-[50%] overflow-hidden md:mr-[10px]"
	>
		<img src="/images/profile_photo.png" alt="The user's avatar" class="h-full object-cover" />
	</div>
	<div
		class="h-full flex-col justify-start text-[1.06rem] gap-[2px] flex-1 min-w-0 mr-[5px] hidden md:flex"
	>
		<div class="text-base font-semibold overflow-hidden text-ellipsis">
			{chatName}
		</div>

		<div
			class="text-[0.9rem] text-gray-600 overflow-hidden text-ellipsis truncate"
			class:is-selected-color={isSelected}
		>
			{$latestMessages[convoID].text}
		</div>
	</div>
	<div
		class="flex-grow-0 flex-shrink-0 basis-auto flex-col gap-[0.8rem] items-end h-full hidden md:flex"
	>
		<div class="text-gray-600 text-[0.9rem]" class:is-selected-color={isSelected}>
			{$latestMessages[convoID].time}
		</div>
		<div class="unread-indicator"></div>
	</div>
</li>

<style>
	/* Style each chat item */
	.chat {
		display: flex;
		align-items: center;
		padding: 0.5rem 1rem;
		border-bottom: 1px solid none;
		height: 80px;
		/* Separator between chats */
	}

	/* Unread message indicator */
	.unread-indicator {
		background-color: #007bff;
		/* Blue background for the indicator */
		color: white;
		/* White text color */
		border-radius: 50%;
		/* Circular shape */
		/* padding: 5px; */
		/* Padding inside the indicator */
		display: flex;
		/* To center the content */
		align-items: center;
		/* Center content vertically */
		justify-content: center;
		/* Center content horizontally */
		width: 0.6rem;
		/* Fixed width */
		height: 0.6rem;
		/* Fixed height */
	}

	.is-selected {
		background-color: #007bff;
		color: white;
	}

	.is-selected-color {
		color: white;
	}
</style>
