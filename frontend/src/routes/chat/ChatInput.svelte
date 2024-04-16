<script lang="ts">
	import { getCurrentTime, formatTime } from '$lib/utils';
	import { sendMessageSocket } from '$lib/websocket';
	import { conversations, latestMessages, selectedConvoID } from '$lib/stores/stores';
	import type { MessageCreate } from '$lib/interfaces/CreateModels.interface';
	import type { LatestMessageInfo } from '$lib/interfaces/UnreadConvo.interface';
	import type { Conversation } from '$lib/interfaces/ResponseModels.interface';
	import { messageStore } from '$lib/stores/messages';
	import { createEventDispatcher } from 'svelte';
	import { websocketNotifStore } from '$lib/stores/websocketNotification';

	let inputValue: string = '';
	let textArea: HTMLTextAreaElement;
	let button: HTMLButtonElement;

	export let senderID: number;
	export let userLang: string;
	export let userName: string;

	const dispatch = createEventDispatcher();

	function resizeTextArea() {
		textArea.style.height = 'auto'; // Temporarily shrink to content size
		textArea.style.height = `${textArea.scrollHeight}px`; // Set to scroll height
	}

	function handleKeyPress(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault(); // Prevent the default action (new line)
			button.click();
		}
	}

	function validateMessage(message: string): boolean {
		// implement more robust validation
		return message.length > 0;
	}

	// Send the message to the server over websockets
	function sendMessage(): void {
		const message: string = inputValue.trim();
		const currConvoID: number = $selectedConvoID;

		if (validateMessage(message) && $selectedConvoID !== -10) {
			const newMessage: MessageCreate = {
				original_text: message,
				sender_id: senderID,
				conversation_id: currConvoID,
				orig_language: userLang,
				sent_at: getCurrentTime(),
				sender_name: userName
			};
			// messages.update((m) => [...m, newMessage]);

			// use this for immediate display first
			const formattedMsg: MessageCreate = {
				conversation_id: currConvoID,
				sender_id: senderID,
				original_text: message,
				orig_language: userLang,
				sent_at: newMessage.sent_at,
				sender_name: null,
				display_photo: true
			};
			messageStore.sendNewMessage(formattedMsg);
			dispatch('msgSent');
			// messageStore.update((state) => {
			// 	const m = state.messages;
			// 	const msgLen = m.length;

			// 	if (
			// 		msgLen > 0 &&
			// 		m[msgLen - 1].sender_id === senderID &&
			// 		differenceInHours(newMessage.sent_at, m[msgLen - 1].sent_at) < 2
			// 	)
			// 		m[msgLen - 1].display_photo = false;

			// 	const formattedMsg: MessageCreate = {
			// 		conversation_id: currConvoID,
			// 		sender_id: senderID,
			// 		original_text: message,
			// 		orig_language: userLang,
			// 		sent_at: newMessage.sent_at,
			// 		sender_name: null,
			// 		display_photo: true
			// 	};

			// 	return {
			// 		...state,
			// 		messages: [...m, formattedMsg],
			// 		offset: state.offset + 1
			// 	};
			// });

			// When we send a msg, the corresponding conversation must be put at top of list
			conversations.update((currConversations) => {
				// Retrieve the current conversation object
				const oldConvo = currConversations.get(currConvoID) as Conversation;

				// needed so the conversation is put at the top
				currConversations.delete(currConvoID);

				currConversations.set(currConvoID, oldConvo);

				return currConversations;
			});

			// sender using websocket.onmessage
			const newMessageInfo: LatestMessageInfo = {
				text: message,
				time: formatTime(newMessage.sent_at), // Format this time as needed
				isRead: 1,
				translationID: -1
			};
			latestMessages.update((messages) => {
				messages[newMessage.conversation_id] = newMessageInfo;
				return messages;
			});

			sendMessageSocket(newMessage); // send message to server

			inputValue = '';
			textArea.style.height = 'auto';
		} else {
			websocketNotifStore.sendNotification('Please enter a message!');
		}
	}
</script>

<!-- Individual Chat Footer for Sending Message -->
{#if $selectedConvoID !== -10}
	<footer>
		<form
			class="flex px-[7px] pb-2 min-[360px]:px-[15px] min-[360px]:pb-4 pt-[12px] bg-neutral-950"
			on:submit|preventDefault={sendMessage}
		>
			<!-- <input
				bind:value={inputValue}
				type="text"
				placeholder="Write a message..."
				class="flex-grow border-solid border border-blue-300 rounded-3xl py-[5px] px-[10px] mr-[10px] focus:outline-none"
			/> -->
			<textarea
				bind:this={textArea}
				bind:value={inputValue}
				placeholder="Write a message..."
				rows="1"
				class="flex-grow resize-none rounded-2xl py-[6px] px-[10px] mr-[5px] min-[360px]:mr-[10px] focus:outline-none max-h-[calc(3em*5)] no-scrollbar text-white bg-neutral-950 border border-neutral-700"
				on:input={resizeTextArea}
				on:keydown={handleKeyPress}
			></textarea>
			<button
				bind:this={button}
				type="submit"
				class="text-white border-none hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:opacity-30 h-fit mt-auto mb-1 sm:ml-1"
				disabled={inputValue.trim().length === 0}
				><svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="w-6 h-6"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5"
					/>
				</svg>
			</button>
		</form>
	</footer>
{/if}
