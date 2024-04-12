<script lang="ts">
	import ChatHeader from './ChatHeader.svelte';
	import ChatInput from './ChatInput.svelte';
	import ConvoSidebar from './ConvoSidebar.svelte';
	import MessagesContainer from './MessagesContainer.svelte';
	import { onMount, onDestroy, tick } from 'svelte';
	import { fade } from 'svelte/transition';
	import { connectWebSocket, closeWebSocket } from '$lib/websocket';
	import {
		selectedConvoID,
		latestMessages,
		conversations,
		currUser,
		displayChatInfo,
		isUserSettings
	} from '$lib/stores/stores';
	import { getMsgPreviewTimeValue } from '$lib/utils';
	import type { S3PreSignedURLPOSTRequest } from '$lib/interfaces/CreateModels.interface';
	import type { LatestMessageInfo } from '$lib/interfaces/UnreadConvo.interface';
	import type {
		Conversation,
		ConversationResponse
	} from '$lib/interfaces/ResponseModels.interface';
	import InfoSidebar from './InfoSidebar.svelte';
	import { languages } from '$lib/languages';
	import clientSettings from '$lib/config/config.client';
	import Cropper from 'cropperjs';
	import 'cropperjs/dist/cropper.css';
	import { goto } from '$app/navigation';
	import LoadingIcon from '$lib/components/LoadingIcon.svelte';
	import { uploadImageToS3 } from '$lib/aws';
	import toast, { Toaster } from 'svelte-french-toast';
	import { websocketNotifStore } from '$lib/stores/websocketNotification';

	export let data;

	// For use to signal when MessageContainer scrolls to the bottom when user clicks a conversation and loads messages
	let msgContainerScrollSignal = false;
	function signalMsgContainerScrollBottom() {
		msgContainerScrollSignal = true;
	}
	function unsignalMsgContainerScrollBottom() {
		msgContainerScrollSignal = false;
	}
	//

	// For use to signal when ConvoSidebar scrolls to top and MessageContainer scrolls to the bottom when user sends a msg
	let convoSidebarScrollSignal = false;
	function signalConvoSidebarMsgContainerScroll() {
		convoSidebarScrollSignal = true; // scroll top
		msgContainerScrollSignal = true; // scroll bottom
	}
	function unsignalConvoSidebarScrollTop() {
		convoSidebarScrollSignal = false;
	}
	//

	// This block of code enables cropping of user's uploaded profile picture for updating profile
	let cropper: Cropper | null;
	let croppedCanvas: HTMLCanvasElement | null;
	let avatarUrl = data.user.presigned_url; // store current profile pic
	let cropElement: HTMLImageElement;
	let cropUrl = ''; // Using Svelte, use variables instead of cropElement.src bc it manages DOM for you
	let showCropModal = false;
	let isLoading = false;

	function initializeCropper() {
		if (cropElement && !cropper) {
			cropper = new Cropper(cropElement, {
				aspectRatio: 1,
				viewMode: 3
			});
		}
	}

	function destroyCropper() {
		if (cropper) {
			cropper.destroy(); // Destroy the old cropper instance
			cropper = null;
		}
	}

	// Function to initialize the cropper when a file is selected
	async function onFileSelected(event: Event) {
		showCropModal = true;
		const input = event.target as HTMLInputElement;

		if (input.files && input.files.length > 0) {
			const file = input.files[0];

			if (file.type !== 'image/jpeg') {
				alert('Only JPG files are allowed.');
				input.value = '';
				showCropModal = false;
				return;
			}

			// selectedFile = file; // Store the selected file

			cropUrl = URL.createObjectURL(file);

			destroyCropper();

			await tick();
			initializeCropper();

			// Clear the value of the file input
			input.value = '';
		}
	}

	async function applyCrop(): Promise<void> {
		showCropModal = false;

		if (cropper) {
			croppedCanvas = cropper.getCroppedCanvas({
				width: 512,
				height: 512,
				fillColor: '#fff'
			});

			avatarUrl = croppedCanvas.toDataURL('image/jpeg', 0.95);

			closeModal();

			if (cropUrl) {
				URL.revokeObjectURL(cropUrl);
			}
		}
	}

	function closeModal(): void {
		showCropModal = false;
		destroyCropper();
	}
	//

	// This function handles logic for updating a user's profile
	async function handleProfileUpdate(): Promise<void> {
		function canvasToBlobPromise(
			canvas: HTMLCanvasElement,
			mimeType = 'image/jpeg',
			quality = 1.0
		): Promise<Blob> {
			return new Promise((resolve, reject) => {
				canvas.toBlob(
					(blob) => {
						if (blob) {
							resolve(blob);
						} else {
							reject(new Error('Blob conversion failed'));
						}
					},
					mimeType,
					quality
				);
			});
		}

		const formData = new FormData();

		if (formPassword) {
			if (formPassword !== formConfirmPW) {
				formErrorMsg = 'Passwords do not match';
				return;
			}

			formData.append('password', formPassword);
		}

		isLoading = true;

		try {
			// 1. If user changed profile, upload to S3 and save the key to access from bucket
			if (croppedCanvas) {
				try {
					// 1. Get presigned URL for POST to S3
					const presignedData: S3PreSignedURLPOSTRequest = {
						filename: 'profile-pic.jpg',
						convo_id: null,
						about: 'Profile picture of user'
					};

					const getPresigned: Response = await fetch(
						`${clientSettings.apiBaseURL}/aws/s3/generate-presigned-post/${false}`,
						{
							method: 'POST',
							headers: {
								Authorization: `Bearer ${data.token}`,
								'Content-Type': 'application/json'
							},
							body: JSON.stringify(presignedData)
						}
					);

					if (!getPresigned.ok) {
						const errorResponse = await getPresigned.json();
						throw new Error(errorResponse.detail);
					}

					const S3Data = await getPresigned.json();

					// 2. Create FormData from the fields of presigned response
					const presignedForm = new FormData();

					// Append the fields from the S3 pre-signed response
					for (const key in S3Data.fields) {
						presignedForm.append(key, S3Data.fields[key]);
					}

					// Append the image; note that 'file' is the key expected by S3 for the file content
					const blob = await canvasToBlobPromise(croppedCanvas, 'image/jpeg');
					presignedForm.append('file', blob);

					// const obj = Object.fromEntries(presignedForm);
					// console.log(obj);

					// 3. Upload image to S3 using the presigned URL and created form
					await uploadImageToS3(S3Data.url, presignedForm);

					// 4. New image uploaded successfully, so update currUser to use this new image as profile picture
					currUser.update((user) => {
						user['presigned_url'] = avatarUrl;

						return user;
					});

					// 5. Save the image key so we can put it in DB
					imageKey = S3Data.fields.key;

					croppedCanvas = null;
				} catch (error) {
					formErrorMsg = 'Failed to upload new profile photo. Please try again.';
					console.error(error);
					return;
				}
			}

			// 2. Either successfully uploaded image or user didn't change profile. Now submit the profile changes (if any) to the backend to save in DB

			if (imageKey) {
				formData.append('profilePhoto', imageKey);
			}

			if (formDefaults.first_name.trim() && formDefaults.first_name.trim() !== $currUser.first_name)
				formData.append('firstname', formDefaults.first_name.trim());
			if (formDefaults.last_name.trim() && formDefaults.last_name.trim() !== $currUser.last_name)
				formData.append('lastname', formDefaults.last_name.trim());
			if (formDefaults.email && formDefaults.email !== $currUser.email)
				formData.append('email', formDefaults.email);
			if (formDefaults.target_language !== $currUser.target_language)
				formData.append('language', formDefaults.target_language);
			if (apiKey.trim()) formData.append('apiKey', apiKey.trim());

			const response: Response = await fetch(`${clientSettings.apiBaseURL}/users/update`, {
				method: 'PATCH',
				headers: {
					Authorization: `Bearer ${data.token}`
				},
				body: formData
			});

			if (!response.ok) {
				formErrorMsg = 'Failed to update profile';
				return;
			}

			formSuccessMsg = 'Profile updated successfully';

			const resData = await response.json();

			if (Object.keys(resData).length !== 0) {
				// Update currUser store with the returned Updated User from backend
				currUser.update((user) => {
					for (const key in resData) {
						// @ts-ignore
						user[key] = resData[key];
					}

					return user;
				});
			}

			// if password was updated, user has to login again
			if (formData.has('password')) goto('../login');

			resetForm(false);
			imageKey = '';
			formErrorMsg = '';
		} catch (error) {
			formErrorMsg = 'Failed to update profile. Try again.';
			console.error('Error updating profile:', error);
		} finally {
			isLoading = false;
		}
	}
	//

	// This chunk of code handles the form UI and form input logic (no submitting when no updated values, resetting the form, etc)
	let formDefaults = { ...data.user };
	let formPassword = '';
	let apiKey = '';
	let formConfirmPW = '';
	let imageKey: string = '';
	let formErrorMsg = '';
	let formSuccessMsg = '';

	// form values are same as current user settings or empty
	$: formValsUnchangedOrEmpty =
		($currUser.first_name === formDefaults.first_name.trim() ||
			formDefaults.first_name.trim() === '') &&
		($currUser.last_name === formDefaults.last_name.trim() ||
			formDefaults.last_name.trim() === '') &&
		($currUser.email === formDefaults.email || formDefaults.email === '') &&
		$currUser.target_language === formDefaults.target_language &&
		!formPassword &&
		!apiKey.trim() &&
		!croppedCanvas;

	function resetForm(clearMessages: boolean): void {
		formDefaults = { ...$currUser }; // Note: could be error where this doesn't reflect the $currUser properly
		formPassword = '';
		apiKey = '';
		formConfirmPW = '';
		avatarUrl = $currUser.presigned_url;
		croppedCanvas = null;

		if (clearMessages) clearFormMessages();
	}

	function clearFormMessages(): void {
		formErrorMsg = '';
		formSuccessMsg = '';
	}
	//

	// This chunk of code sets the value of stores to be used in other components when a user first enters the chat page
	latestMessages.set(
		data.user.top_n_convos.reduce(
			(acc: Record<number, LatestMessageInfo>, conversation: ConversationResponse) => {
				if (conversation.latest_message && conversation.latest_message.relevant_translation) {
					acc[conversation.id] = {
						text: conversation.latest_message.relevant_translation,
						time: getMsgPreviewTimeValue(conversation.latest_message.sent_at),
						isRead: conversation.latest_message.is_read as number,
						translationID: conversation.latest_message.translation_id as number
					};
				}
				return acc;
			},
			{}
		)
	);

	currUser.set({
		id: data.user.id,
		first_name: data.user.first_name,
		last_name: data.user.last_name,
		profile_photo: data.user.profile_photo,
		email: data.user.email,
		target_language: data.user.target_language,
		is_admin: data.user.is_admin,
		presigned_url: data.user.presigned_url
	});

	conversations.set(
		data.user.top_n_convos.reduce(
			(acc: Map<number, Conversation>, conversation: ConversationResponse) => {
				acc.set(conversation.id, {
					convoName: conversation.conversation_name,
					isGroupChat: conversation.is_group_chat,
					presignedUrl: conversation.presigned_url
				});
				return acc;
			},
			new Map()
		)
	);
	//

	// Toast notifications for Websocket errors and notifications
	$: if ($websocketNotifStore.visible) {
		toast.error($websocketNotifStore.message, {
			duration: 5000
		});
		websocketNotifStore.reset();
	}
	//

	onMount(() => {
		toast.remove();
		connectWebSocket(data.user.websocket_token, data.user.email, data.token);
	});

	onDestroy(() => {
		closeWebSocket();
		destroyCropper();
		if (cropUrl) {
			URL.revokeObjectURL(cropUrl);
		}
	});
</script>

<Toaster />

<main class="messaging-app bg-neutral-900">
	<!-- Conversations List -->
	<ConvoSidebar
		currEmail={data.user.email}
		token={data.token}
		scrollSignal={convoSidebarScrollSignal}
		on:initMsgFetch={signalMsgContainerScrollBottom}
		on:scrolledTop={unsignalConvoSidebarScrollTop}
	/>

	<!-- Actual Chat Area -->
	{#if $selectedConvoID !== -10}
		<section class="chat-area w-full max-w-full min-w-0">
			<ChatHeader token={data.token} />
			<MessagesContainer
				currUserID={data.user.id}
				token={data.token}
				scrollBottomSignal={msgContainerScrollSignal}
				on:scrolledBottom={unsignalMsgContainerScrollBottom}
			/>
			<ChatInput
				senderID={data.user.id}
				userLang={data.user.target_language}
				userName={`${data.user.first_name} ${data.user.last_name}`}
				on:msgSent={signalConvoSidebarMsgContainerScroll}
			/>
		</section>
		<!-- Update User Profile Section -->
	{:else if $isUserSettings}
		<!-- Modal for Cropping Uploaded Profile Pic -->
		{#if showCropModal}
			<!-- New -->
			<!-- <div
				class="opacity-50 fixed left-0 top-0 z-30 w-screen h-screen bg-black"
				transition:fade={{ duration: 250 }}
			></div>
			<div
				class="block overflow-x-hidden overflow-y-auto fixed left-0 top-0 z-40 w-full h-full overflow-hidden outline-none"
				transition:fade={{ duration: 250 }}
			>
				<div class="relative w-auto pointer-events-none mx-auto my-7 sm:max-w-lg">
					<div
						class="relative flex flex-col w-full pointer-events-auto bg-white bg-clip-border border border-solid border-gray-700 rounded outline-none"
					>
						<div
							class="flex text-lg font-bold justify-center p-4 border-b border-solid border-b-gray-400"
						>
							<h1>Crop Photo</h1>
						</div>

						<div class="relative flex-auto p-4">
							<div>
								<img
									bind:this={cropElement}
									src={cropUrl}
									alt="Crop this"
									class="max-w-full align-middle border-none"
								/>
							</div>
						</div>

						<div
							class="flex flex-wrap items-center justify-end p-4 border-t border-solid border-t-gray-300"
						>
							<button
								on:click|preventDefault={closeModal}
								class="w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
								>Cancel</button
							>
							<button
								on:click|preventDefault={applyCrop}
								class="w-full justify-center rounded-md bg-blue-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:opacity-90 sm:ml-3 sm:w-auto"
								>Crop</button
							>
						</div>
					</div>
				</div>
			</div> -->
			<!-- New -->

			<!-- svelte-ignore a11y-click-events-have-key-events -->
			<!-- svelte-ignore a11y-no-static-element-interactions -->
			<div
				transition:fade={{ duration: 250 }}
				class="fixed left-0 top-0 bg-black bg-opacity-50 w-screen h-screen flex justify-center items-center z-30"
			>
				<div
					on:click|stopPropagation
					class="bg-white rounded shadow-md p-6 w-auto max-w-[90%] sm:max-w-xl sm:m-0 flex flex-col gap-5 bg-clip-border border border-solid border-gray-700"
				>
					<div class="flex text-lg font-bold justify-center">
						<h1>Crop Photo</h1>
					</div>

					<div class="flex-1">
						<img
							bind:this={cropElement}
							src={cropUrl}
							alt="Crop this"
							class="max-w-full object-contain"
						/>
					</div>

					<div
						class="flex flex-wrap items-center justify-end px-4 pt-4 border-t border-solid border-t-gray-300 gap-3"
					>
						<button
							on:click|preventDefault={closeModal}
							class="w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
							>Cancel</button
						>
						<button
							on:click|preventDefault={applyCrop}
							class="w-full justify-center rounded-md bg-blue-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:opacity-90 sm:w-auto"
							>Crop</button
						>
					</div>
				</div>
			</div>
		{/if}

		<!-- User Profile Update Form UI -->
		<section
			class="space-y-6 px-4 pt-4 min-[400px]:px-10 min-[400px]:pt-8 w-full overflow-scroll pb-4 min-[450px]:pb-0 bg-neutral-950 text-white"
		>
			<div class="space-y-1">
				<h2 class="text-2xl font-bold tracking-tight">Settings</h2>
				<p class="text-neutral-300">Manage your account settings.</p>
			</div>
			<hr class="border-t border-neutral-500" />
			<form
				class="rounded-xl min-[450px]:px-8 min-[450px]:pb-5 space-y-5"
				on:submit|preventDefault={handleProfileUpdate}
				on:input={clearFormMessages}
			>
				<div class="flex flex-col justify-center items-center mb-7">
					<label
						for="profilePhoto"
						class="relative overflow-hidden rounded-full w-11/12 min-[450px]:w-52 group cursor-pointer"
					>
						{#if avatarUrl}
							<img
								src={avatarUrl}
								alt="User's Avatar"
								class="w-full object-cover transition-opacity duration-300 ease-in-out group-hover:opacity-50"
							/>
						{:else}
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke-width="1.1"
								stroke="currentColor"
								class="w-full object-cover transition-opacity duration-300 ease-in-out group-hover:opacity-50"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
								/>
							</svg>
						{/if}
						<span
							class="absolute inset-0 flex justify-center items-center opacity-0 transition-opacity duration-300 ease-in-out group-hover:opacity-100 text-white text-center text-[0.8rem] bg-black bg-opacity-20"
							>Upload Profile Picture (JPG only)</span
						>
					</label>
					<input
						id="profilePhoto"
						name="profilePhoto"
						type="file"
						accept=".jpg,.jpeg"
						class="hidden"
						on:change={onFileSelected}
					/>
				</div>

				<div class="flex flex-col sm:flex-row gap-2">
					<div class="sm:w-1/2 space-y-2">
						<label for="firstname" class="block text-sm font-bold"> First Name </label>
						<input
							bind:value={formDefaults.first_name}
							type="text"
							name="firstName"
							id="firstname"
							maxlength="100"
							class="border border-neutral-700 rounded w-full py-2 px-3 leading-tight focus:outline-none bg-neutral-950"
						/>
					</div>
					<div class="sm:w-1/2 space-y-2">
						<label for="lastname" class="block text-sm font-bold"> Last Name </label>
						<input
							bind:value={formDefaults.last_name}
							type="text"
							name="lastName"
							id="lastname"
							maxlength="100"
							class="border border-neutral-700 bg-neutral-950 rounded w-full py-2 px-3 leading-tight focus:outline-none"
						/>
					</div>
				</div>

				<div class="space-y-2">
					<label for="email" class="block text-sm font-bold"> Email </label>
					<input
						bind:value={formDefaults.email}
						type="email"
						name="email"
						id="email"
						class="border border-neutral-700 bg-neutral-950 rounded w-full py-2 px-3 leading-tight focus:outline-none"
					/>
				</div>

				<div class="space-y-2">
					<label for="language" class="block text-sm font-bold"> Language </label>
					<select
						bind:value={formDefaults.target_language}
						id="language"
						name="language"
						class="border border-neutral-700 bg-neutral-950 rounded-sm w-full min-[450px]:w-1/2 focus:outline-none pl-2 py-1"
					>
						{#each languages as language}
							<option value={language}>{language}</option>
						{/each}
					</select>
					<p class="text-[0.8rem] text-neutral-300">
						Messages sent to you will be translated to this language.
					</p>
				</div>

				<div class="space-y-2">
					<label for="apiKey" class="block text-sm font-bold"> New OpenAI API Key </label>
					<input
						bind:value={apiKey}
						type="text"
						name="apiKey"
						id="apiKey"
						class="border border-neutral-700 bg-neutral-950 rounded w-full py-2 px-3 leading-tight focus:outline-none"
					/>
				</div>

				<div class="space-y-2">
					<label for="password" class="block text-sm font-bold"> New Password </label>
					<input
						bind:value={formPassword}
						type="password"
						name="password"
						id="password"
						class="border border-neutral-700 bg-neutral-950 rounded w-full py-2 px-3 leading-tight focus:outline-none"
					/>
				</div>

				<div class="space-y-2">
					<label
						for="confPassword"
						class="block text-sm font-bold"
						class:opacity-30={formPassword.length === 0}
					>
						Confirm Password
					</label>
					<input
						disabled={formPassword.length === 0}
						bind:value={formConfirmPW}
						type="password"
						name="confPassword"
						id="confPassword"
						class="border border-neutral-700 bg-neutral-950 rounded w-full py-2 px-3 leading-tight focus:outline-none disabled:cursor-not-allowed disabled:opacity-30"
					/>
				</div>

				<div class="flex flex-col items-center justify-center mt-4 gap-2">
					<div class="space-x-3">
						<button
							disabled={formValsUnchangedOrEmpty}
							class="rounded bg-white py-2 px-4 text-black ring-1 ring-inset ring-gray-400 hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-30"
							on:click|preventDefault={() => resetForm(true)}
						>
							Reset
						</button>
						<button
							type="submit"
							disabled={formValsUnchangedOrEmpty}
							class="text-white mt-2 py-2 px-4 rounded bg-blue-700 hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-30"
							>Update</button
						>
					</div>
					{#if formErrorMsg}
						<p class="text-[0.8rem] text-red-600" class:hidden={formValsUnchangedOrEmpty}>
							{formErrorMsg}
						</p>
					{:else if formSuccessMsg}
						<p class="text-[0.8rem] text-blue-700">
							{formSuccessMsg}
						</p>
					{:else if isLoading}
						<LoadingIcon size="w-7 h-7" />
					{:else}
						<p class="text-[0.8rem] text-neutral-200" class:hidden={formValsUnchangedOrEmpty}>
							* Unsaved Changes
						</p>
					{/if}
				</div>
			</form>
		</section>
	{/if}

	<!-- Info Sidebar of a Specific Conversation -->
	{#if $displayChatInfo}
		<InfoSidebar token={data.token} />
	{/if}
</main>

<style>
	.messaging-app {
		display: flex;
		height: 100vh;
		/* Full height of the viewport */
	}

	/* ------------------- Chat area styles -------------------*/
	.chat-area {
		display: flex;
		flex-direction: column;
		/* Set a fixed width for the chat area or adjust as needed */
		height: 100vh;
		/* Border to separate from the rest of the interface */
	}
</style>
