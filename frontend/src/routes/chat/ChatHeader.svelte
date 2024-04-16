<script lang="ts">
	import { onMount } from 'svelte';
	import {
		selectedConvoID,
		selectedConvo,
		displayChatInfo,
		changeChatName,
		conversations
	} from '$lib/stores/stores';
	import { isPresignedExpired, refreshGETPresigned } from '$lib/aws';
	import clientSettings from '$lib/config/config.client';
	import { websocketNotifStore } from '$lib/stores/websocketNotification';

	export let token: string;
	let newName: string = '';

	async function checkChatUrl(): Promise<void> {
		if ($selectedConvo?.presignedUrl && isPresignedExpired($selectedConvo.presignedUrl)) {
			const convoID = $selectedConvoID;

			try {
				// {"convo_id": "presigned_URL"}
				const newGCUrl = await refreshGETPresigned('convo_id', [convoID], token);

				conversations.update((currConversations) => {
					const prevVal = currConversations.get(convoID);

					if (prevVal) {
						currConversations.set(convoID, { ...prevVal, presignedUrl: newGCUrl[convoID] });
					}

					return currConversations;
				});
			} catch (error) {
				return;
			}
		}
	}

	async function toggleDisplayChat(): Promise<void> {
		// check if GC url expired
		await checkChatUrl();

		displayChatInfo.set(!$displayChatInfo);
	}

	function handleClickOutside() {
		changeChatName.set(false);
		newName = '';
	}

	onMount(() => {
		window.addEventListener('click', handleClickOutside);
		return () => {
			window.removeEventListener('click', handleClickOutside);
		};
	});

	async function submitNewName() {
		try {
			newName = newName.trim();

			if (newName.length > 0) {
				const response: Response = await fetch(
					`${clientSettings.apiBaseURL}/conversations/${$selectedConvoID}/update`,
					{
						method: 'PATCH',
						headers: {
							Authorization: `Bearer ${token}`,
							'Content-Type': 'application/json'
						},
						body: JSON.stringify({ conversation_name: newName })
					}
				);

				if (!response.ok) throw new Error();

				// conversations.update((currConversations) => {
				// 	if (currConversations.has($selectedConvoID)) {
				// 		// Retrieve the current conversation object
				// 		const oldConvo = currConversations.get($selectedConvoID) as Conversation;

				// 		// Update only the convoName field, keeping other fields intact
				// 		const newConversation: Conversation = {
				// 			...oldConvo, // Spread operator to copy existing fields
				// 			convoName: newName // Overwrite convoName with new value
				// 		};

				// 		// Set the updated conversation object back in the map
				// 		currConversations.set($selectedConvoID, newConversation);
				// 	}

				// 	return currConversations;
				// });

				newName = '';
				changeChatName.set(false);
			}
		} catch (error) {
			websocketNotifStore.sendNotification(
				`Error updating group chat name. Please try again in a moment`
			);
		}
	}
</script>

<!-- Individual Chat Header -->
{#if $selectedConvoID !== -10}
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<header
		class="flex items-center justify-between py-[15px] px-[10px] gap-4 min-[555px]:px-[20px] bg-neutral-950 text-white border-b-[0.5px] border-neutral-500 sticky"
	>
		<div class="flex items-center min-w-0 w-full gap-2">
			<div class="chat-photo">
				{#if $selectedConvo?.presignedUrl}
					<img
						src={$selectedConvo?.presignedUrl}
						alt="The conversation's profile"
						class="w-full overflow-hidden rounded-full"
					/>
				{:else if $selectedConvo?.isGroupChat}
					<!-- Group Chat Icon -->
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1"
						stroke="currentColor"
						class="w-full"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z"
						/>
					</svg>
				{:else}
					<!-- Non-group Chat Icon -->
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.1"
						stroke="currentColor"
						class="w-full"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
						/>
					</svg>
				{/if}
			</div>

			{#if $changeChatName}
				<form class="flex w-full" on:submit={submitNewName}>
					<!-- svelte-ignore a11y-autofocus -->
					<input
						bind:value={newName}
						on:click|stopPropagation
						autofocus
						required
						type="text"
						class="w-full border-none outline-none p-[5px] bg-neutral-950"
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
					{$selectedConvo?.convoName}
				</div>
			{/if}
		</div>

		{#if $selectedConvo?.isGroupChat}
			<!-- svelte-ignore a11y-click-events-have-key-events -->
			<div class="flex-shrink-0" on:click={toggleDisplayChat}>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="w-8 h-8 cursor-pointer"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M6.75 12a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0ZM12.75 12a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0ZM18.75 12a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z"
					/>
				</svg>
			</div>
		{/if}
	</header>
	<!-- <hr class="self-center border-b w-[95%] border-b-gray-300" /> -->
{/if}

<style>
	.chat-photo {
		width: 40px;
		height: 40px;
		min-width: 40px;
		overflow: hidden;
		display: flex;
		justify-content: center;
		align-items: center;
		margin-right: 10px;
	}
</style>
