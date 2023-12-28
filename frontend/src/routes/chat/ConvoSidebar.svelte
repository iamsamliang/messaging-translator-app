<script lang="ts">
	import type { ConversationCreate, MessageCreate } from '$lib/interfaces/CreateModels.interface';
	import Convo from './Convo.svelte';
	import { fade } from 'svelte/transition';
	import { selectedConvo, latestMessages, messages } from '$lib/stores/stores';
	import type { IConvo } from '$lib/interfaces/iconvo.interface';
	import { formatTime } from '$lib/utils';

	export let currEmail: string;
	export let convos: IConvo[];

	let showModal: boolean = false;
	let peoples: string = '';

	function createChat(): void {
		showModal = true;
	}

	async function populateMessages(convoID: number): Promise<void> {
		try {
			const response: Response = await fetch(`http://localhost:8000/messages/${convoID}`, {
				method: 'GET',
				credentials: 'include'
			});
			if (!response.ok) {
				const errorResponse = await response.json();
				console.error('Error details:', JSON.stringify(errorResponse.detail, null, 2));
				throw new Error(`Error code: ${response.status}`);
			}

			const data: MessageCreate[] = await response.json();
			const updatedMessages = data.map((message: MessageCreate) => ({
				...message,
				sent_at: formatTime(message.sent_at)
			}));
			messages.set(updatedMessages);

			// get rid of new notifications indicator for this selected group chat
			// latestMessages.update((unreads) => {
			// 	delete unreads[convoID];
			// 	return unreads;
			// });
		} catch (error) {
			console.error('Error fetching messages:', error);
			messages.set([]); // Set messages to an empty array in case of error
		}
	}

	async function handleCreateChat(): Promise<void> {
		const chatName: string = peoples.trim();
		if (chatName.length > 255) {
			alert('Chat Name is too long');
			return;
		}

		const emails: string[] = chatName.split(',');
		emails.push(currEmail);
		console.log(emails);

		const createdChat: ConversationCreate = {
			conversation_name: chatName,
			user_ids: emails
		};

		try {
			const response: Response = await fetch('http://localhost:8000/conversations', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(createdChat)
			});

			if (!response.ok) {
				const errorResponse = await response.json();
				console.error('Error details:', errorResponse);
				throw new Error(`Error code: ${response.status}`);
			}

			const data: any = await response.json();
			const updaterVal: IConvo = {
				conversation_name: chatName,
				id: data.id
			};
			selectedConvo.update(() => updaterVal);
			// selectedConvoID = data.id;

			const newConvo: IConvo = {
				conversation_name: data.conversation_name,
				id: data.id
			};

			convos = [newConvo, ...convos];
		} catch (error) {
			console.error('There was a problem with the fetch operation:', error);
			// Optionally handle the error (e.g., show an error message to the user)
		}

		showModal = false;
		peoples = '';
	}

	function closeModal(): void {
		showModal = false;
		peoples = '';
	}

	function handleSubmit(): void {
		handleCreateChat();
	}

	async function handleClick(convo: IConvo): Promise<void> {
		selectedConvo.set(convo);
		await populateMessages(convo.id);
	}
</script>

{#if showModal}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div
		on:click={closeModal}
		transition:fade={{ duration: 250 }}
		class="fixed left-0 top-0 bg-black bg-opacity-50 w-screen h-screen flex justify-center items-center"
	>
		<div
			on:click|stopPropagation
			class="bg-white rounded shadow-md p-8 w-[30%] flex flex-col gap-5"
		>
			<div class="text-lg font-bold">
				<h1>Create New Chat</h1>
			</div>
			<form on:submit|preventDefault={handleSubmit}>
				<div>
					<!-- svelte-ignore a11y-autofocus -->
					<input
						autofocus
						required
						type="text"
						bind:value={peoples}
						placeholder="Enter emails, separated by commas"
						class="w-full"
					/>
				</div>
				<div class="px-4 pt-3 sm:flex sm:flex-row-reverse sm:px-6">
					<button
						type="submit"
						class="inline-flex w-full justify-center rounded-md bg-blue-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-350 sm:ml-3 sm:w-auto"
						>Create</button
					>
					<button
						type="button"
						on:click|preventDefault={closeModal}
						class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
						>Cancel</button
					>
				</div>
			</form>
		</div>
	</div>
{/if}

<!-- Sidebar for chats -->
<aside class="chats-sidebar">
	<!-- Sidebar Header -->
	<header class="chats-sidebar-header">
		<!-- Search bar -->
		<div class="chats-search-bar">
			<input type="text" placeholder="Search..." />
		</div>

		<!-- Create new chat button -->
		<div class="create-chat-btn-container">
			<button
				class="place-content-center text-blue-400"
				aria-label="New chat"
				on:click|preventDefault={createChat}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="w-6 h-6 place-content-center"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"
					/>
				</svg>
			</button>
		</div>
		<!-- Using a plus sign for simplicity -->
	</header>

	<!-- Chat list -->
	<ul class="p-3">
		{#each convos as convo}
			<Convo
				convoID={convo.id}
				chatName={convo.conversation_name}
				isSelected={$selectedConvo?.id === convo.id}
				on:click={() => handleClick(convo)}
			/>
		{/each}
	</ul>
</aside>

<style>
	/* Set up the sidebar with a background color, text color, and padding */
	.chats-sidebar {
		width: 25%;
		border-right: 1px solid #ccc;
	}

	/* Style the sidebar header to display its children inline */
	.chats-sidebar-header {
		display: flex;
		/* Use flexbox for layout */
		/* justify-content: space-between; */
		/* Space out the search bar and new chat button */
		align-items: center;
		/* Vertically center items in the header */

		padding-top: 1rem;
		padding-bottom: 0.2rem;
	}

	/* Style the search container for the input and search button */
	.chats-search-bar {
		display: flex;
		/* Align the search input and button inline */
		padding-left: 1rem;
		width: 80%;
		/* Allow the search container to fill the space */
	}

	/* Style the search input field */
	.chats-search-bar input[type='text'] {
		width: 100%;
		/* Full width of the container */
		padding: 0.5rem;
		/* Padding inside the input field */
		border: 1px solid #333;
		/* Border to make it stand out */
		border-radius: 4px;
		/* Rounded corners */
	}

	.create-chat-btn-container {
		display: flex;
		justify-content: center;
		/* Aligns the button to the right */
		width: 20%;
		/* Takes the full width of its parent */
	}

	.chats-search-bar,
	.create-chat-btn-container {
		height: 36px;
	}

	/* Add a hover effect for buttons */
	button:hover {
		opacity: 0.9;
		/* Slightly transparent on hover */
	}
</style>
