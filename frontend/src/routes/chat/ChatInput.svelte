<script lang="ts">
	import { getCurrentTime, formatTime } from '$lib/utils';
	import { sendMessageSocket } from '$lib/websocket';
	import { conversations, latestMessages, messages, selectedConvoID } from '$lib/stores/stores';
	import type { MessageCreate } from '$lib/interfaces/CreateModels.interface';
	import type { LatestMessageInfo } from '$lib/interfaces/UnreadConvo.interface';
	import type { Conversation } from '$lib/interfaces/ResponseModels.interface';
	import { differenceInHours } from 'date-fns';

	let inputValue: string = '';
	let textArea: HTMLTextAreaElement;
	let button: HTMLButtonElement;

	export let senderID: number;
	export let userLang: string;
	export let userName: string;

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
			messages.update((m) => {
				const msgLen = m.length;
				const arePrevMsgs = msgLen > 0;
				const sameSenderAsPrev = m[msgLen - 1].sender_id === senderID;
				const within2Hours = differenceInHours(newMessage.sent_at, m[msgLen - 1].sent_at) < 2;

				if (arePrevMsgs && sameSenderAsPrev && within2Hours) m[msgLen - 1].display_photo = false;

				const formattedMsg: MessageCreate = {
					conversation_id: currConvoID,
					sender_id: senderID,
					original_text: message,
					orig_language: userLang,
					sent_at: newMessage.sent_at,
					sender_name: null,
					display_photo: true
				};

				m = [...m, formattedMsg];

				return m;
			});

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
			alert('Please enter a message!');
		}
	}
</script>

<!-- Individual Chat Footer for Sending Message -->
{#if $selectedConvoID !== -10}
	<footer>
		<form
			class="flex px-[10px] pb-[11px] pt-[14px] bg-white border-t border-solid border-gray-200"
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
				class="flex-grow resize-none border-solid border border-blue-300 rounded-xl py-[6px] px-[10px] mr-[10px] focus:outline-none max-h-[calc(3em*5)] no-scrollbar"
				on:input={resizeTextArea}
				on:keydown={handleKeyPress}
			></textarea>
			<button
				bind:this={button}
				type="submit"
				class="bg-blue-600 text-white border-none py-1 px-5 rounded-full hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:opacity-30 h-fit mt-auto"
				disabled={inputValue.trim().length === 0}>Send</button
			>
		</form>
	</footer>
{/if}
