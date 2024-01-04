<script lang="ts">
	import type { ConversationCreate, MessageCreate } from '$lib/interfaces/CreateModels.interface';
	import Convo from './Convo.svelte';
	import { fade } from 'svelte/transition';
	import { selectedConvo, latestMessages, messages } from '$lib/stores/stores';
	import type { IConvo } from '$lib/interfaces/iconvo.interface';
	import { formatTime } from '$lib/utils';

	export let currEmail: string;
	export let convos: IConvo[];

	let input = '';
	let emails: string[] = [];
	let emailsErrorMsg: string = '';
	let showModal: boolean = false;
	let chatName: string;
	// let peoples: string = '';

	async function handleClick(convo: IConvo): Promise<void> {
		selectedConvo.set(convo);
		await populateMessages(convo.id);
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

			// get rid of new notifications indicator for this selected group chat if there are any
			if (!$latestMessages[convoID].isRead) {
				latestMessages.update((messages) => {
					messages[convoID]['isRead'] = 1;
					return messages;
				});

				// notify server of this update
				const translation_id = $latestMessages[convoID].translationID;
				const patchData = { is_read: 1 };
				const patchResponse: Response = await fetch(
					`http://localhost:8000/translations/${translation_id}`,
					{
						method: 'PATCH',
						headers: {
							'Content-Type': 'application/json'
						},
						credentials: 'include',
						body: JSON.stringify(patchData)
					}
				);
				if (!patchResponse.ok) {
					const errorResponse = await patchResponse.json();
					console.error('Error details:', JSON.stringify(errorResponse.detail, null, 2));
					throw new Error(`Error code: ${patchResponse.status}`);
				}
			}
		} catch (error) {
			console.error('Error fetching messages:', error);
			messages.set([]); // Set messages to an empty array in case of error
		}
	}

	const addEmail = () => {
		// Trim and remove trailing commas
		let emailToAdd = input.trim().replace(/,$/, '');
		// Simple email validation check and avoid duplicates
		if (
			emailToAdd &&
			/^\S+@\S+\.\S+$/.test(emailToAdd) &&
			!emails.includes(emailToAdd) &&
			emailToAdd !== currEmail
		) {
			emails = [...emails, emailToAdd];
			input = ''; // Clear input after adding
			emailsErrorMsg = '';
		} else {
			emailsErrorMsg = 'Please enter a valid email address';
		}
	};

	const removeEmail = (emailToRemove: string) => {
		emails = emails.filter((email_new) => email_new !== emailToRemove);
	};

	// Prepend email when the user types a comma or presses Enter
	const handleInput = (event: KeyboardEvent) => {
		if (event.key === 'Enter' || event.key === ',') {
			event.preventDefault(); // Prevent form submission or other default behaviors
			if (!input.trim()) return; // If the input is only whitespace, do nothing
			addEmail();
		}
	};

	async function handleCreateChat(): Promise<void> {
		if (chatName.length > 255) {
			alert('Chat Name is too long');
			return;
		}

		if (emails.length === 0) {
			alert('You must add at least 1 user');
			return;
		}

		emails.push(currEmail);

		const createdChat: ConversationCreate = {
			conversation_name: chatName.trim(),
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
		emails = [];
		input = '';
		chatName = '';
		emailsErrorMsg = '';
	}

	function openModal(): void {
		showModal = true;
	}

	function closeModal(): void {
		showModal = false;
		emails = [];
		input = '';
		chatName = '';
		emailsErrorMsg = '';
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
			class="bg-white rounded shadow-md p-8 w-[80%] md:w-[65%] lg:w-[55%] xl:w-[50%] 2xl:w-[45%] flex flex-col gap-5"
		>
			<div class="flex text-lg font-bold justify-center">
				<h1>Create New Chat</h1>
			</div>
			<!-- Implicitly awaits the async function -->
			<form on:submit|preventDefault={handleCreateChat}>
				<div class="flex flex-wrap items-center p-[5px] rounded gap-1">
					<!-- <input
						autofocus
						required
						type="text"
						bind:value={peoples}
						placeholder="Enter emails, separated by commas"
						class="w-full"
						/> -->

					<!-- svelte-ignore a11y-autofocus -->
					<input
						autofocus
						required
						type="text"
						class="w-full p-[5px] mb-2 border-none outline-none"
						bind:value={chatName}
						placeholder="Chat names"
					/>
					{#each emails as email}
						<span class="bg-blue-500 text-white py-[5px] px-[10px] rounded-md flex items-center">
							{email}
							<button
								on:click={() => removeEmail(email)}
								class="bg-transparent border-none text-white ml-[5px] cursor-pointer"
								>&times;</button
							>
						</span>
					{/each}
					<input
						type="text"
						class="flex-grow border-none outline-none p-[5px]"
						bind:value={input}
						on:keydown={handleInput}
						placeholder="User emails"
					/>
				</div>
				{#if emailsErrorMsg}
					<div
						class="flex justify-center text-red-500 text-sm transition-opacity duration-300 ease-in-out"
						transition:fade={{ duration: 100 }}
					>
						{emailsErrorMsg}
					</div>
				{/if}
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
<aside class="chats-sidebar min-w-fit md:min-w-[400px] max-w-[400px]">
	<!-- Sidebar Header -->
	<header class="chats-sidebar-header">
		<div class="pl-4 w-[80%] h-[36px] hidden md:flex">
			<input
				type="text"
				placeholder="Search..."
				class="w-full p-2 rounded-md border-solid border-blue-500 border focus:outline-none"
			/>
		</div>

		<!-- Create new chat button -->
		<div class="flex justify-center w-full md:w-[20%] md:h-[36px]">
			<button
				class="place-content-center text-blue-400"
				aria-label="New chat"
				on:click|preventDefault={openModal}
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
		border-right: 1px solid #ccc;
		/* min-width: 25%; */
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

	/* Add a hover effect for buttons */
	button:hover {
		opacity: 0.9;
		/* Slightly transparent on hover */
	}
</style>
