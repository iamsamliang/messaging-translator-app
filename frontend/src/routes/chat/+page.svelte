<script lang="ts">
	import ChatHeader from './ChatHeader.svelte';
	import ChatInput from './ChatInput.svelte';
	import ConvoSidebar from './ConvoSidebar.svelte';
	import MessagesContainer from './MessagesContainer.svelte';
	import { onMount, onDestroy } from 'svelte';
	import { connectWebSocket, closeWebSocket } from '$lib/websocket';
	import { currUserID, selectedConvo, latestMessages } from '$lib/stores/stores';
	import { formatTime } from '$lib/utils';
	import type { LatestMessageInfo } from '$lib/interfaces/UnreadConvo.interface';

	export let data;

	latestMessages.set(
		data.user.conversations.reduce((acc: Record<number, LatestMessageInfo>, conversation: any) => {
			acc[conversation.id] = {
				text: conversation.latest_message.relevant_translation,
				time: formatTime(conversation.latest_message.sent_at)
			};
			return acc;
		}, {})
	);
	currUserID.set(data.user.id);

	onMount(() => {
		connectWebSocket();
	});

	onDestroy(() => {
		closeWebSocket();
	});
</script>

<main class="messaging-app">
	<ConvoSidebar currEmail={data.user.email} convos={data.user.conversations} />

	<!-- Actual Chat Area -->
	{#if $selectedConvo}
		<section class="chat-area">
			<ChatHeader />
			<MessagesContainer currUserID={data.user.id} />
			<ChatInput
				senderID={data.user.id}
				userLang={data.user.target_language}
				firstName={data.user.first_name}
				lastName={data.user.last_name}
			/>

			<!-- Individual Chat Content for Group Chats-->
			<!-- <div class="message-container">
            <div class="message">
                <div class="message-sender-photo"></div>
                <div class="message-sender-name"></div>
                <div class="message-content"></div>
                <div class="message-time"></div>
            </div>
        </div> -->
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
		width: 75%;
		/* Set a fixed width for the chat area or adjust as needed */
		height: 100vh;
		border-left: 1px solid #ccc;
		/* Border to separate from the rest of the interface */
	}
</style>
