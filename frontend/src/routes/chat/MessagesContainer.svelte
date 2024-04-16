<script lang="ts">
	import { selectedConvoID } from '$lib/stores/stores';
	import { createEventDispatcher, tick } from 'svelte';
	import Message from './Message.svelte';
	import { isSameDay, differenceInHours } from 'date-fns';
	import { getDateSeparator, formatTime } from '$lib/utils';
	import type { MessageCreate } from '$lib/interfaces/CreateModels.interface';
	import LazyList from '$lib/components/LazyList.svelte';
	import { messageStore } from '$lib/stores/messages';
	import clientSettings from '$lib/config/config.client';
	import { msgContainerScrollSignal } from '$lib/stores/msgContainerScrollSignal';

	export let currUserID: number;
	export let token: string;

	// Process chat messages in messageStore to include date separators
	$: processedMsgs = $messageStore.messages.reduce((acc: MessageCreate[], message, index) => {
		let prevMsgDate = index > 0 ? $messageStore.messages[index - 1].sent_at : null;
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
	//

	// This block of code is used to ensure the MessageContainer is scrolled to the bottom when we initially fetch messages and when we send a new message
	export let scrollBottomSignal: boolean;
	const dispatch = createEventDispatcher();
	let messagesContainer: HTMLDivElement;
	async function scrollToBottom() {
		await tick();
		messagesContainer.scrollTop = messagesContainer.scrollHeight;
	}
	$: if (scrollBottomSignal) {
		scrollToBottom();
		dispatch('scrolledBottom');
	}

	// Detect when new messages arrive and scroll down
	$: if ($msgContainerScrollSignal) {
		scrollToBottom();
		msgContainerScrollSignal.reset();
	}
</script>

<div class="message-container no-scrollbar gap-1 bg-neutral-950" bind:this={messagesContainer}>
	<!-- Repeat this 'message' div for each message in the chat -->
	<!-- {#each processedMsgs as message}
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
	{/each} -->

	<!-- New -->
	<LazyList
		items={processedMsgs}
		loadedAll={$messageStore.loadedAll}
		root={messagesContainer}
		rootMargin="100px"
		let:item
		on:loadMore={async () =>
			messageStore.fetchMsgs(
				$selectedConvoID,
				$messageStore.offset,
				clientSettings.fetchMsgBatchSize,
				$messageStore.loadedAll,
				token,
				messagesContainer
			)}
	>
		{#if item.separator}
			<div class="flex justify-center text-sm text-neutral-400 mt-3">
				{item.separator[0]}
				{item.separator[1]}
			</div>
		{/if}
		<Message
			content={item.original_text}
			time={formatTime(item.sent_at)}
			senderID={item.sender_id}
			{currUserID}
			senderName={item.sender_name}
			displayPhoto={item.display_photo}
		/>
	</LazyList>
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
