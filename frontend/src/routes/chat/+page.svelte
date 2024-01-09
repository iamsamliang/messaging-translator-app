<script lang="ts">
	import ChatHeader from './ChatHeader.svelte';
	import ChatInput from './ChatInput.svelte';
	import ConvoSidebar from './ConvoSidebar.svelte';
	import MessagesContainer from './MessagesContainer.svelte';
	import { onMount, onDestroy } from 'svelte';
	import { connectWebSocket, closeWebSocket } from '$lib/websocket';
	import { currUserID, selectedConvo, latestMessages, conversations } from '$lib/stores/stores';
	import { formatTime } from '$lib/utils';
	import type { LatestMessageInfo } from '$lib/interfaces/UnreadConvo.interface';
	import type { Conversation } from '$lib/interfaces/ConvoList.interface';

	export let data;

	latestMessages.set(
		data.user.conversations.reduce((acc: Record<number, LatestMessageInfo>, conversation: any) => {
			if (conversation.latest_message) {
				acc[conversation.id] = {
					text: conversation.latest_message.relevant_translation,
					time: formatTime(conversation.latest_message.sent_at),
					isRead: conversation.latest_message.is_read,
					translationID: conversation.latest_message.translation_id
				};
			}
			return acc;
		}, {})
	);
	currUserID.set(data.user.id);
	conversations.set(
		data.user.conversations.reduce((acc: Map<number, Conversation>, conversation: any) => {
			acc.set(conversation.id, { convoName: conversation.conversation_name });
			return acc;
		}, new Map())
	);

	onMount(() => {
		connectWebSocket();
	});

	onDestroy(() => {
		closeWebSocket();
	});
</script>

<main class="messaging-app">
	<ConvoSidebar currEmail={data.user.email} />

	<!-- Actual Chat Area -->
	{#if $selectedConvo}
		<section class="chat-area w-full max-w-full min-w-0">
			<ChatHeader />
			<MessagesContainer currUserID={data.user.id} />
			<ChatInput
				senderID={data.user.id}
				userLang={data.user.target_language}
				firstName={data.user.first_name}
				lastName={data.user.last_name}
			/>
		</section>
	{/if}
</main>

<style>
	.messaging-app {
		display: flex;
		height: 100vh;
		/* Full height of the viewport */
	}

	/* ------------------- Chat area styles -------------------*/
	.chat-area {
		display: flex;
		flex-direction: column;
		/* Set a fixed width for the chat area or adjust as needed */
		height: 100vh;
		border-left: 1px solid #ccc;
		/* Border to separate from the rest of the interface */
	}
</style>
