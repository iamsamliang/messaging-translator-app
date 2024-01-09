<script lang="ts">
	// get the chat photo from the backend

	import { conversations, selectedConvo } from '$lib/stores/stores';
	import { onMount } from 'svelte';
	import type { IConvo } from '$lib/interfaces/iconvo.interface';

	let showDropdown: boolean = false;
	let changeName: boolean = false;
	let newName: string = '';

	function handleClickOutside() {
		showDropdown = false;
		changeName = false;
	}

	function toggleDropDown() {
		showDropdown = !showDropdown;
	}

	function handleName() {
		showDropdown = false;
		changeName = true;
	}

	onMount(() => {
		window.addEventListener('click', handleClickOutside);
		return () => {
			window.removeEventListener('click', handleClickOutside);
		};
	});

	async function submitNewName() {
		try {
			const response: Response = await fetch(
				`http://localhost:8000/conversations/${$selectedConvo?.id}/update-name`,
				{
					method: 'PATCH',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({ conversation_name: newName.trim() })
				}
			);

			if (!response.ok) {
				const errorResponse = await response.json();
				console.error('Error details:', errorResponse);
				throw new Error(`Error code: ${response.status}`);
			}

			const modConvo: IConvo = {
				id: $selectedConvo?.id,
				conversation_name: newName.trim()
			};

			selectedConvo.set(modConvo);
			conversations.update((currConversations) => {
				if (currConversations.has(modConvo.id)) {
					currConversations.set(modConvo.id, { convoName: modConvo.conversation_name });
				}
				return currConversations;
			});

			newName = '';
			changeName = false;
		} catch (error) {
			console.error('There was a problem with the fetch operation:', error);
			// Optionally handle the error (e.g., show an error message to the user)
		}
	}
</script>

<!-- Individual Chat Header -->
{#if $selectedConvo}
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<header
		class="flex items-center justify-between p-[10px] bg-white border-b border-solid border-gray-200"
	>
		<div class="flex items-center min-w-0 w-full">
			<div class="chat-photo">
				<img src="/images/profile_photo.png" alt="The user's avatar" />
			</div>
			{#if changeName}
				<form class="flex w-full" on:submit={submitNewName}>
					<input
						bind:value={newName}
						on:click|stopPropagation
						autofocus
						required
						type="text"
						class="w-full border-none outline-none p-[5px]"
					/>
					<!-- <button
						bind:this={button}
						type="submit"
						class="send-message"
						disabled={inputValue.trim().length === 0}>Send</button
					> -->
				</form>
			{:else}
				<div class="font-bold overflow-hidden text-ellipsis">
					{$selectedConvo.conversation_name}
				</div>
			{/if}
		</div>
		<!-- svelte-ignore a11y-click-events-have-key-events -->
		<div class="flex-shrink-0" on:click|stopPropagation={toggleDropDown}>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="1.5"
				stroke="currentColor"
				class="w-6 h-6 cursor-pointer"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z"
				/>
			</svg>
			{#if showDropdown}
				<div class="absolute right-2 mt-4 bg-black shadow-xl z-10 hover:bg-gray-900 rounded-sm">
					<ul>
						<li>
							<button on:click|stopPropagation={handleName} class="block px-4 py-2 text-white"
								>Change Chat Name
							</button>
						</li>
					</ul>
				</div>
			{/if}
		</div>
	</header>
{/if}

<style>
	.chat-photo {
		width: 40px;
		height: 40px;
		min-width: 40px;
		border-radius: 50%;
		overflow: hidden;
		display: flex;
		justify-content: center;
		align-items: center;
		margin-right: 10px;
	}

	.chat-photo img {
		width: auto;
		height: 100%;
		min-width: 100%;
		object-fit: cover;
	}
</style>
