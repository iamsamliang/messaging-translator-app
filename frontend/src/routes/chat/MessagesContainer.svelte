<script lang="ts">
	import { messages } from '$lib/stores/stores';
	import Message from './Message.svelte';

	// first get message data from backend
	// then populate each Message component with the content and timestamp of that message
	// use a `each` loop to create multiple Message components
</script>

<div class="message-container">
	<!-- Repeat this 'message' div for each message in the chat -->
	{#each $messages as message}
		<Message content={message.content} time={message.time} fromCurrUser={message.fromCurrUser} />
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
