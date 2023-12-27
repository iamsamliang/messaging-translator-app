<script lang="ts">
	import { getCurrentTime } from '$lib/utils';
	import { sendMessageSocket } from '$lib/websocket';
	import { messages, selectedConvo } from '$lib/stores/stores';
	import type { MessageCreate } from '$lib/interfaces/CreateModels.interface';

	let inputValue: string = '';
	export let senderID: number;
	export let userLang: string;
	export let firstName: string;
	export let lastName: string;

	function validateMessage(message: string): boolean {
		// implement more robust validation
		return message.length > 0;
	}

	// Send the message to the server over websockets
	function sendMessage(): void {
		const message: string = inputValue.trim();

		if (validateMessage(message) && $selectedConvo) {
			// use this for immediate display first
			const newMessage: MessageCreate = {
				original_text: message,
				sender_id: senderID,
				conversation_id: $selectedConvo.id,
				orig_language: userLang,
				sent_at: getCurrentTime(),
				first_name: firstName,
				last_name: lastName
			};
			messages.update((m) => [...m, newMessage]);

			sendMessageSocket(newMessage); // send message to server

			inputValue = '';
		} else {
			alert('Please enter a message!');
		}
	}
</script>

<!-- Individual Chat Footer for Sending Message -->
{#if $selectedConvo}
	<footer>
		<form class="message-input-area" on:submit|preventDefault={sendMessage}>
			<input bind:value={inputValue} type="text" placeholder="Write a message..." />
			<button type="submit" class="send-message">Send</button>
		</form>
	</footer>
{/if}

<style>
	button:hover {
		opacity: 0.9; /* Slightly transparent on hover */
	}

	.message-input-area {
		display: flex;
		padding: 10px;
		background-color: #f7f7f7;
		border-top: 1px solid #ccc;
	}

	.message-input-area input[type='text'] {
		flex-grow: 1;
		border: 1px solid #ccc;
		border-radius: 18px;
		padding: 5px 10px;
		margin-right: 10px;
	}

	.send-message {
		background-color: #007bff;
		color: white;
		border: none;
		border-radius: 18px;
		padding: 5px 15px;
		cursor: pointer;
	}
</style>
