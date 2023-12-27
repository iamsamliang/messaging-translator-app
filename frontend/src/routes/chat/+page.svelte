<script lang="ts">
	import ChatHeader from './ChatHeader.svelte';
	import ChatInput from './ChatInput.svelte';
	import ConvoSidebar from './ConvoSidebar.svelte';
	import MessagesContainer from './MessagesContainer.svelte';
	import { onMount, onDestroy } from 'svelte';
	import { connectWebSocket, closeWebSocket } from '$lib/websocket';
	import { currUserID, selectedConvo } from '$lib/stores/stores';

	export let data;

	onMount(() => {
		currUserID.set(data.user.id);
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
