<script lang="ts">
	import { messages } from '$lib/stores/stores';
	import { onMount, tick } from 'svelte';
	import Message from './Message.svelte';

	// first get message data from backend
	// then populate each Message component with the content and timestamp of that message
	// use a `each` loop to create multiple Message components
	export let currUserID: number;

	let messagesContainer: HTMLDivElement;

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

<div class="message-container no-scrollbar overscroll-contain" bind:this={messagesContainer}>
	<!-- Repeat this 'message' div for each message in the chat -->
	{#each $messages as message}
		<Message
			content={message.original_text}
			time={message.sent_at}
			senderID={message.sender_id}
			{currUserID}
		/>
	{/each}
	<!-- Add more messages as needed -->
</div>

<style>
	.message-container {
		display: flex;
		flex-direction: column;
		flex-grow: 1;
		overflow-y: auto;
		padding: 10px;
		background-color: #ffe8e8;
	}
</style>
