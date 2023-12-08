<script lang="ts">
	import type { IMessage } from '$lib/interfaces/imessage.interface';
	import { messages } from '$lib/stores/stores';
	import { getCurrentTime } from '$lib/utils';

	let inputValue = '';

	function validateMessage(message: string): boolean {
		// implement more robust validation
		return message.length > 0;
	}

	function addMessageToContainer(message: string): void {
		const newMessage: IMessage = {
			content: message,
			time: getCurrentTime(),
			fromCurrUser: true
		};
		messages.update((m) => [...m, newMessage]);
	}

	// Send the message to the server over websockets
	function sendMessage(): void {
		const message: string = inputValue.trim();

		if (validateMessage(message)) {
			addMessageToContainer(message);
			// send message to server here
			// send message function //
			inputValue = '';
		} else {
			alert('Please enter a message!');
		}
	}
</script>

<!-- Individual Chat Footer for Sending Message -->
<footer>
	<form class="message-input-area" on:submit|preventDefault={sendMessage}>
		<input bind:value={inputValue} type="text" placeholder="Write a message..." />
		<button type="submit" class="send-message">Send</button>
	</form>
</footer>

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
