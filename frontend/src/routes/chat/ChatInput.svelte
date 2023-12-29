<script lang="ts">
	import { getCurrentTime } from '$lib/utils';
	import { sendMessageSocket } from '$lib/websocket';
	import { latestMessages, messages, selectedConvo } from '$lib/stores/stores';
	import type { MessageCreate } from '$lib/interfaces/CreateModels.interface';
	import type { LatestMessageInfo } from '$lib/interfaces/UnreadConvo.interface';

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

			// update UI for the Conversation block in the Conversation lists. Need this otherwise too slow to update for
			// sender using websocket.onmessage
			const newMessageInfo: LatestMessageInfo = {
				text: message,
				time: newMessage.sent_at // Format this time as needed
			};
			latestMessages.update((messages) => {
				messages[newMessage.conversation_id] = newMessageInfo;
				return messages;
			});

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
		<form
			class="flex p-[10px] bg-white border-t border-solid border-gray-200"
			on:submit|preventDefault={sendMessage}
		>
			<input
				bind:value={inputValue}
				type="text"
				placeholder="Write a message..."
				class="flex-grow border-solid border border-blue-300 rounded-3xl py-[5px] px-[10px] mr-[10px] focus:outline-none"
			/>
			<button type="submit" class="send-message" disabled={inputValue.trim().length === 0}
				>Send</button
			>
		</form>
	</footer>
{/if}

<style>
	button:hover {
		opacity: 0.9; /* Slightly transparent on hover */
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
