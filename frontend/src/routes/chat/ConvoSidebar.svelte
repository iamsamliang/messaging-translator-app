<script lang="ts">
	import type { ConversationCreate } from '$lib/interfaces/CreateModels.interface';
	import Convo from './Convo.svelte';
	import { fade } from 'svelte/transition';
	import {
		selectedConvoID,
		selectedConvo,
		latestMessages,
		conversations,
		convoMembers,
		currUser,
		displayChatInfo,
		isUserSettings,
		sortedConvoMemberIDs
	} from '$lib/stores/stores';
	import { derived } from 'svelte/store';
	import type {
		Conversation,
		ConversationResponse,
		GetMembersResponse
	} from '$lib/interfaces/ResponseModels.interface';
	import { isPresignedExpired, refreshGETPresigned } from '$lib/aws';
	import VirtualScroll from '$lib/components/VirtualScroll.svelte';
	import { getMsgPreviewTimeValue } from '$lib/utils';
	import clientSettings from '$lib/config/config.client';
	import { messageStore } from '$lib/stores/messages';
	import { createEventDispatcher, tick } from 'svelte';

	export let currEmail: string;

	// type ConversationEntry = [number, Conversation];
	// const convosArray = derived(conversations, ($conversations): ConversationEntry[] =>
	// 	Array.from($conversations.entries()).reverse()
	// );

	// Scrolling to the top of Convo list when user sends a message
	export let scrollSignal: boolean;
	const dispatch = createEventDispatcher();
	let vs: VirtualScroll;
	$: if (scrollSignal) {
		vs.scrollToOffset(0);
		dispatch('scrolledTop');
	}

	const convosArray = derived(conversations, ($conversations) => {
		return Array.from($conversations.entries())
			.map(([id, convo]) => ({
				id: id,
				convo: convo
			}))
			.reverse();
	});

	let height = 80;

	let isLoadingConvos = false;
	let loadedAll = false;
	// let virtualScrollList: VirtualScroll;
	// let listContainer: HTMLDivElement;

	// offset by however much we already loaded initially
	let convosOffset = clientSettings.initialConversationLoadLimit;
	const visibleCount = 40; // # of Convo components to render in DOM
	const LIMIT = 30;

	let input = '';
	let emails: string[] = [];
	let emailsErrorMsg: string = '';
	let showModal: boolean = false;
	let chatName: string = '';

	// async function onScrollHandler(): Promise<void> {
	// 	console.log(virtualScrollList.getOffset());

	// 	if (listContainer.scrollHeight - virtualScrollList.getOffset() < 500) {
	// 		console.log('loading more items');
	// 	}
	// }

	async function fetchConversations(): Promise<void> {
		if (isLoadingConvos || loadedAll) return;

		isLoadingConvos = true;

		// console.log($conversations);
		console.log('fetching more convos');
		const response: Response = await fetch(
			`${clientSettings.apiBaseURL}/conversations?offset=${convosOffset}&limit=${LIMIT}`,
			{
				method: 'GET',
				credentials: 'include'
			}
		);
		if (!response.ok) {
			const errorResponse = await response.json();
			console.error('Error details:', JSON.stringify(errorResponse.detail, null, 2));
			throw new Error(`Error code: ${response.status}`);
		}

		// should return an array of Convos
		const newConversations: ConversationResponse[] = await response.json();

		conversations.update((currConvos) => {
			const newConvosMap: Map<number, Conversation> = new Map();

			latestMessages.update((latestMsg) => {
				for (let conversation of newConversations) {
					newConvosMap.set(conversation.id, {
						convoName: conversation.conversation_name,
						isGroupChat: conversation.is_group_chat,
						presignedUrl: conversation.presigned_url
					});

					if (conversation.latest_message && conversation.latest_message.relevant_translation) {
						latestMsg[conversation.id] = {
							text: conversation.latest_message.relevant_translation,
							time: getMsgPreviewTimeValue(conversation.latest_message.sent_at),
							isRead: conversation.latest_message.is_read as number,
							translationID: conversation.latest_message.translation_id as number
						};
					}
				}

				return latestMsg;
			});

			currConvos.forEach((convo, convo_id) => {
				newConvosMap.set(convo_id, convo);
			});

			return newConvosMap;
		});

		// console.log($conversations);
		// console.log('\n');

		if (newConversations.length < LIMIT) loadedAll = true;

		convosOffset += newConversations.length;
		isLoadingConvos = false;
	}

	async function openUserSettings(): Promise<void> {
		// check expiration time of presigned URL for current user
		if ($currUser.presigned_url) {
			if (isPresignedExpired($currUser.presigned_url)) {
				try {
					const newURLs = await refreshGETPresigned('user_ids', [$currUser.id]);
					currUser.update((user) => {
						user = { ...user, presigned_url: newURLs[user.id] };

						return user;
					});
				} catch (error) {
					console.error('Error refreshing current user GET presigned URL:', error);
				}
			}
		}

		selectedConvoID.set(-10);
		displayChatInfo.set(false);
		isUserSettings.set(true);
	}

	async function handleClick(convoID: number): Promise<void> {
		await getMembers(convoID);

		if (convoID !== $selectedConvoID) {
			// messages.set([]);
			messageStore.reset();
			selectedConvoID.set(convoID);

			if (!$selectedConvo?.isGroupChat) {
				displayChatInfo.set(false);
			}

			await populateMessages(convoID);
		}
	}

	async function getMembers(convoID: number): Promise<void> {
		try {
			const response: Response = await fetch(
				`${clientSettings.apiBaseURL}/conversations/${convoID}/members`,
				{
					method: 'GET',
					credentials: 'include'
				}
			);
			if (!response.ok) {
				const errorResponse = await response.json();
				console.error('Error details:', JSON.stringify(errorResponse.detail, null, 2));
				throw new Error(`Error code: ${response.status}`);
			}

			// { "members": members_dict, "sorted_member_ids": sorted_member_ids, "gc_url": gc_url }
			const membersData: GetMembersResponse = await response.json();

			// update chat presigned URL
			conversations.update((currConversations) => {
				const prevVal = currConversations.get(convoID);

				if (prevVal) {
					currConversations.set(convoID, { ...prevVal, presignedUrl: membersData.gc_url });
				}

				return currConversations;
			});

			convoMembers.set(membersData.members);

			currUser.update((user) => {
				user = { ...user, presigned_url: membersData.members[user.id].presigned_url };

				return user;
			});

			sortedConvoMemberIDs.set(membersData.sorted_member_ids);
		} catch (error) {
			console.error('Error fetching chat members:', error);
		}
	}

	async function populateMessages(convoID: number): Promise<void> {
		try {
			// const response: Response = await fetch(`${clientSettings.apiBaseURL}/messages/${convoID}`, {
			// 	method: 'GET',
			// 	credentials: 'include'
			// });
			// if (!response.ok) {
			// 	const errorResponse = await response.json();
			// 	console.error('Error details:', JSON.stringify(errorResponse.detail, null, 2));
			// 	throw new Error(`Error code: ${response.status}`);
			// }

			// const data: MessageCreate[] = await response.json();

			// messages.set(data);

			await messageStore.fetchMsgs(
				convoID,
				$messageStore.offset,
				clientSettings.initialMessageLoadLimit,
				$messageStore.loadedAll
			);
			dispatch('initMsgFetch');

			// get rid of new notifications indicator for this selected group chat if there are any
			if ($latestMessages[convoID]) {
				if (!$latestMessages[convoID].isRead) {
					latestMessages.update((messages) => {
						messages[convoID]['isRead'] = 1;
						return messages;
					});

					// notify server of this update
					const translation_id = $latestMessages[convoID].translationID;
					const patchData = { is_read: 1 };
					const patchResponse: Response = await fetch(
						`${clientSettings.apiBaseURL}/translations/${translation_id}`,
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
			}
		} catch (error) {
			console.error('Error fetching messages:', error);
			messageStore.reset();
			// messages.set([]);
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
		if (event.key === 'Enter' || event.key === ',' || event.key === 'Tab') {
			event.preventDefault(); // Prevent form submission or other default behaviors
			if (!input.trim()) return; // If the input is only whitespace, do nothing
			addEmail();
		}
	};

	async function handleCreateChat(): Promise<void> {
		if (emails.length === 0) {
			alert('You must add at least 1 user');
			return;
		}

		emails.push(currEmail); // add self

		const isGroupChat = emails.length >= 3;
		let convoNameCreateVal: string | null = null;

		if (isGroupChat) convoNameCreateVal = chatName.trim();

		const createdChat: ConversationCreate = {
			conversation_name: convoNameCreateVal,
			user_ids: emails,
			is_group_chat: isGroupChat
		};

		try {
			const response: Response = await fetch(`${clientSettings.apiBaseURL}/conversations/create`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				credentials: 'include',
				body: JSON.stringify(createdChat)
			});

			if (!response.ok) {
				const errorResponse = await response.json();
				if (response.status === 404) {
					emailsErrorMsg = errorResponse.detail;
					emails.pop();
					input = '';
					return;
				} else {
					console.error('Error details:', errorResponse);
					throw new Error(`Error code: ${response.status}`);
				}
			}

			const data: any = await response.json();

			// duplicate chat
			// if (data.existing_id) {
			// 	await handleClick(data.existing_id);
			// } else {
			conversations.update((currConversations) => {
				currConversations.set(data.id, {
					convoName: data.conversation_name,
					isGroupChat: data.is_group_chat,
					presignedUrl: data.presigned_url
				});
				return currConversations;
			});

			let desiredOffset = 0;

			for (const element of $convosArray) {
				if (element.id === data.id) break;
				desiredOffset += vs.getSize(element.id);
			}

			await handleClick(data.id); // update ChatHeader and MessageContainer
			// }

			vs.scrollToOffset(desiredOffset);

			showModal = false;
			emails = [];
			input = '';
			chatName = '';
			emailsErrorMsg = '';
		} catch (error) {
			console.error('Error creating chat:', error);
			// Optionally handle the error (e.g., show an error message to the user)
		}
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
		class="fixed left-0 top-0 bg-black bg-opacity-50 w-screen h-screen flex justify-center items-center z-30"
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
				<div class="flex flex-wrap items-center p-[5px] rounded gap-3">
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
					<!-- svelte-ignore a11y-autofocus -->
					<input
						autofocus
						type="text"
						class="flex-grow border-none outline-none p-[5px]"
						bind:value={input}
						on:keydown={handleInput}
						placeholder="User emails [Add with 'Enter' or 'Tab' or 'Comma']"
					/>

					<input
						hidden={emails.length < 2}
						required={emails.length >= 2}
						type="text"
						class="w-full p-[5px] border-none outline-none"
						bind:value={chatName}
						maxlength="255"
						placeholder="Group chat name"
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
						disabled={emails.length === 0 || (emails.length >= 2 && chatName.trim().length === 0)}
						class="inline-flex w-full justify-center rounded-md bg-blue-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:opacity-90 sm:ml-3 sm:w-auto disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:opacity-30"
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
<aside
	class="border-r border-black flex flex-col min-w-fit min-[1047px]:min-w-[400px] max-w-[400px]"
>
	<!-- Sidebar Header -->
	<!-- min-[1047px]:border-b-[1px] min-[1047px]:border-b-cyan-300 -->
	<header
		class="flex flex-col min-[1047px]:flex-row items-center pt-1 min-[1047px]:pt-3 min-[1047px]:pb-1 gap-2 bg-neutral-900 text-white"
	>
		<!-- <div class="pl-4 w-[80%] h-[36px] hidden min-[1047px]:flex">
			<input
				type="text"
				placeholder="Search..."
				class="w-full p-2 rounded-md border-solid border-blue-500 border focus:outline-none"
			/>
		</div> -->
		<div class="flex items-center justify-center min-[1047px]:justify-start mx-3 min-[1047px]:mx-0">
			<div
				class="min-[1047px]:ml-6 min-[1047px]:mr-4 my-1 mb-2 w-14 h-14 rounded-full overflow-hidden flex justify-center"
			>
				{#if $currUser.presigned_url}
					<img src={$currUser.presigned_url} alt="User Settings" class="w-full" />
				{:else}
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
			<h1 class="text-lg hidden min-[1047px]:flex text-neutral-100">
				{$currUser.first_name}
				{$currUser.last_name}
			</h1>
		</div>

		<div
			class="flex flex-col justify-center items-center w-full min-[1047px]:w-[20%] min-[1047px]:h-[36px] min-[1047px]:justify-end min-[1047px]:flex-grow min-[1047px]:mr-6 gap-3 min-[1047px]:flex-row"
		>
			<!-- Open User Settings -->
			<button
				class="place-content-center text-neutral-200"
				aria-label="Open user settings"
				on:click|preventDefault={openUserSettings}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.2"
					stroke="currentColor"
					class="w-9 h-9 place-content-center"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z"
					/>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
					/>
				</svg>
			</button>

			<!-- Create new chat button -->
			<button
				class="place-content-center text-neutral-200"
				aria-label="New chat"
				on:click|preventDefault={openModal}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.2"
					stroke="currentColor"
					class="w-9 h-9 place-content-center"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10"
					/>
				</svg>
			</button>
		</div>
	</header>

	<!-- Chat list -->
	<!-- <ul class="p-3">
		{#each $convosArray as [convoID, convo]}
			<Convo
				{convoID}
				chatName={convo.convoName}
				isSelected={$selectedConvoID === convoID}
				isGroupChat={convo.isGroupChat}
				url={convo.presignedUrl}
				on:click={() => handleClick(convoID)}
			/>
		{/each}
	</ul> -->

	<div class="p-3 h-full overflow-y-auto overscroll-contain no-scrollbar bg-neutral-900">
		<VirtualScroll
			bind:this={vs}
			data={$convosArray}
			key="id"
			keeps={visibleCount}
			bottomThreshold={700}
			estimateSize={height}
			let:data
			on:bottom={fetchConversations}
		>
			<Convo
				convoID={data.id}
				chatName={data.convo.convoName}
				isSelected={$selectedConvoID === data.id}
				isGroupChat={data.convo.isGroupChat}
				url={data.convo.presignedUrl}
				itemHeight={height}
				on:click={() => handleClick(data.id)}
			/>
		</VirtualScroll>
	</div>

	<!-- Go to User Settings -->
	<!-- <button
		class="mt-auto flex items-center group border-t-2 border-t-gray-300 cursor-pointer justify-center min-[1047px]:justify-start"
		on:click={openUserSettings}
	>
		<div class="min-[1047px]:ml-4 min-[1047px]:mr-3 my-2 w-12 h-12 rounded-full overflow-hidden">
			{#if $currUser.presigned_url}
				<img
					src={$currUser.presigned_url}
					alt="User Settings"
					class="w-full transition-transform duration-400 ease-in-out group-hover:scale-110 group-hover:shadow-glow"
				/>
			{:else}
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.1"
					stroke="currentColor"
					class="w-full transition-transform duration-400 ease-in-out group-hover:scale-110 group-hover:shadow-glow"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
					/>
				</svg>
			{/if}
		</div>
		<h1
			class="text-lg transition-transform duration-400 ease-in-out group-hover:scale-105 hidden min-[1047px]:flex"
		>
			{$currUser.first_name}
			{$currUser.last_name}
		</h1>
	</button> -->
</aside>

<style>
	/* Set up the sidebar with a background color, text color, and padding */
	/* .chats-sidebar {
		border-right: 1px solid #ccc;
	} */

	/* Add a hover effect for buttons */
	button:hover {
		opacity: 0.9;
		/* Slightly transparent on hover */
	}
</style>
