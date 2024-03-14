<script lang="ts">
	import { messages } from '$lib/stores/stores';
	import { onMount, tick } from 'svelte';
	import Message from './Message.svelte';
	import { isSameDay, differenceInHours } from 'date-fns';
	import { getDateSeparator, formatTime } from '$lib/utils';
	import type { MessageCreate } from '$lib/interfaces/CreateModels.interface';

	export let currUserID: number;

	let messagesContainer: HTMLDivElement;

	// process messages to include date separators
	$: processedMsgs = $messages.reduce((acc: MessageCreate[], message, index) => {
		let prevMsgDate = index > 0 ? $messages[index - 1].sent_at : null;
		let separator = null;

		if (prevMsgDate) {
			const isSame = isSameDay(message.sent_at, prevMsgDate);
			const isOver2Hours = differenceInHours(message.sent_at, prevMsgDate) >= 2;

			if (!isSame || isOver2Hours) {
				separator = getDateSeparator(message.sent_at);
			}
		} else {
			// Always add a separator for the first message or if prevMsgDate is not defined
			separator = getDateSeparator(message.sent_at);
		}

		acc.push({ ...message, separator });
		return acc;
	}, []);

	// Scroll to bottom function
	async function scrollToBottom() {
		await tick();
		messagesContainer.scrollTop = messagesContainer.scrollHeight;
	}

	// Reactive statement to handle new messages
	$: if ($messages) {
		scrollToBottom();
	}

	// Ensure scrolling to bottom on initial load
	onMount(async () => {
		await scrollToBottom();
	});
</script>

<div
	class="message-container no-scrollbar overscroll-contain gap-1 bg-neutral-100"
	bind:this={messagesContainer}
>
	<!-- Repeat this 'message' div for each message in the chat -->
	{#each processedMsgs as message}
		{#if message.separator}
			<div class="flex justify-center text-sm text-gray-600 mt-3">
				{message.separator[0]}
				{message.separator[1]}
			</div>
		{/if}
		<Message
			content={message.original_text}
			time={formatTime(message.sent_at)}
			senderID={message.sender_id}
			{currUserID}
			senderName={message.sender_name}
			displayPhoto={message.display_photo}
		/>
	{/each}
</div>

<style>
	.message-container {
		display: flex;
		flex-direction: column;
		flex-grow: 1;
		overflow-y: auto;
		padding: 10px;
	}
</style>
