<script lang="ts">
	import {
		changeChatName,
		convoMembers,
		currUser,
		selectedConvo,
		selectedConvoID,
		sortedConvoMemberIDs
	} from '$lib/stores/stores';
	import { onDestroy, tick } from 'svelte';
	import { fade } from 'svelte/transition';
	import Cropper from 'cropperjs';
	import 'cropperjs/dist/cropper.css';
	import type { S3PreSignedURLPOSTRequest } from '$lib/interfaces/CreateModels.interface';
	import { isPresignedExpired, refreshGETPresigned, uploadImageToS3 } from '$lib/aws';
	import LoadingIcon from '$lib/components/LoadingIcon.svelte';
	import clientSettings from '$lib/config/config.client';
	import { websocketNotifStore } from '$lib/stores/websocketNotification';

	export let token: string;

	let showMembers: boolean = false;

	let showModal: boolean = false;
	let emails: string[] = [];
	let input = '';
	let emailsErrorMsg: string = '';

	let deleteConfirm: boolean = false;
	let leaveGroup: boolean = false;
	let deleteEmail: string = '';

	//////////////////////////////////////////////////////////////////////////////////////

	let showCropModal: boolean = false;
	let cropUrl = '';
	let cropper: Cropper | null;
	let cropElement: HTMLImageElement;
	let croppedCanvas: HTMLCanvasElement | null;
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
				websocketNotifStore.sendNotification('Only JPG files are allowed.');
				input.value = '';
				showCropModal = false;
				return;
			}

			if (cropUrl) URL.revokeObjectURL(cropUrl);
			cropUrl = URL.createObjectURL(file);

			destroyCropper();

			await tick();
			initializeCropper();

			// Clear the value of the file input
			input.value = '';
		}
	}

	async function applyCrop(): Promise<void> {
		if (cropper) {
			isLoading = true;

			croppedCanvas = cropper.getCroppedCanvas({
				width: 512,
				height: 512,
				fillColor: '#fff'
			});

			// const groupUrl = croppedCanvas.toDataURL('image/jpeg', 0.95);

			croppedCanvas.toBlob(
				async (blob) => {
					try {
						if (blob === null) throw new Error('Blob is null');

						// 1. Get presigned URL for POST to S3
						const presignedData: S3PreSignedURLPOSTRequest = {
							filename: 'group-chat-pic.jpg',
							convo_id: $selectedConvoID,
							about: `Profile picture for group chat ${$selectedConvoID}`
						};

						const getPresigned: Response = await fetch(
							`${clientSettings.apiBaseURL}/aws/s3/generate-presigned-post/${true}`,
							{
								method: 'POST',
								headers: {
									'Content-Type': 'application/json',
									Authorization: `Bearer ${token}`
								},
								body: JSON.stringify(presignedData)
							}
						);

						if (!getPresigned.ok) throw new Error();

						const S3Data = await getPresigned.json();

						// 2. Create FormData from the fields of presigned response
						const presignedForm = new FormData();

						// Append the fields from the S3 pre-signed response
						for (const key in S3Data.fields) {
							presignedForm.append(key, S3Data.fields[key]);
						}

						// Append the image; note that 'file' is the key expected by S3 for the file content
						presignedForm.append('file', blob);

						// 3. Upload image to S3 using the presigned URL and created form
						await uploadImageToS3(S3Data.url, presignedForm);

						// 4. Update backend with the Key
						const response: Response = await fetch(
							`${clientSettings.apiBaseURL}/conversations/${$selectedConvoID}/update`,
							{
								method: 'PATCH',
								headers: {
									'Content-Type': 'application/json',
									Authorization: `Bearer ${token}`
								},
								body: JSON.stringify({ conversation_photo: S3Data.fields.key })
							}
						);

						if (!response.ok) throw new Error();

						// 5. Update the conversation to store the new image as picture
						// conversations.update((currConversations) => {
						// 	const prevVal = currConversations.get($selectedConvoID);

						// 	if (prevVal)
						// 		currConversations.set($selectedConvoID, { ...prevVal, presignedUrl: groupUrl });

						// 	return currConversations;
						// });

						closeCropModal();
						if (cropUrl) URL.revokeObjectURL(cropUrl);
						croppedCanvas = null;
					} catch (error) {
						websocketNotifStore.sendNotification(
							'Failed to change group chat photo. Please try again.'
						);
						return;
					} finally {
						isLoading = false;
					}
				},
				'image/jpeg',
				1.0
			);
		}
	}

	function closeCropModal(): void {
		showCropModal = false;
		destroyCropper();
	}

	onDestroy(() => {
		destroyCropper();
		if (cropUrl) {
			URL.revokeObjectURL(cropUrl);
		}
	});

	//////////////////////////////////////////////////////////////////////////////////////

	function leaveConfirmation() {
		leaveGroup = true;
		showModal = true;
	}

	function deleteConfirmation(delEmail: string, name: string) {
		showModal = true;
		deleteConfirm = true;
		deleteEmail = delEmail;
		input = name;
	}

	const addEmail = () => {
		// Trim and remove trailing commas
		let emailToAdd = input.trim().replace(/,$/, '');
		// Simple email validation check and avoid duplicates
		if (
			emailToAdd &&
			/^\S+@\S+\.\S+$/.test(emailToAdd) &&
			!emails.includes(emailToAdd) &&
			emailToAdd !== $currUser.email
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

	async function openModal(): Promise<void> {
		showModal = true;

		if (!showMembers) {
			await checkMemberURLs();
			showMembers = true;
		}
	}

	function closeModal(): void {
		showModal = false;
		deleteConfirm = false;
		deleteEmail = '';
		leaveGroup = false;
		emails = [];
		input = '';
		emailsErrorMsg = '';
	}

	// Prepend email when the user types a comma or presses Enter
	const handleInput = (event: KeyboardEvent) => {
		if (event.key === 'Enter' || event.key === ',' || event.key === 'Tab') {
			event.preventDefault(); // Prevent form submission or other default behaviors
			if (!input.trim()) return; // If the input is only whitespace, do nothing
			addEmail();
		}
	};

	async function checkMemberURLs(): Promise<void> {
		const expiredIDs: number[] = [];
		const copyMembers = { ...$convoMembers };
		const currUserID = $currUser.id;

		// need this bc the value for the current user could be "self" instead of url
		copyMembers[currUserID].presigned_url = $currUser.presigned_url;

		for (const memberID in copyMembers) {
			const member = copyMembers[Number(memberID)];
			if (member.presigned_url && isPresignedExpired(member.presigned_url))
				expiredIDs.push(member.id);
		}

		if (expiredIDs.length !== 0) {
			try {
				const newURLs = await refreshGETPresigned('user_ids', expiredIDs, token);

				convoMembers.update((currMembers) => {
					const updatedMembers = { ...currMembers };

					for (const memberID in newURLs) {
						const id = Number(memberID);

						updatedMembers[id] = { ...updatedMembers[id], presigned_url: newURLs[id] };
					}

					return updatedMembers;
				});

				if (currUserID in newURLs) {
					currUser.update((user) => {
						user = { ...user, presigned_url: newURLs[currUserID] };

						return user;
					});
				}
			} catch (error) {
				return;
			}
		}
	}

	async function getMembers(): Promise<void> {
		if (!showMembers) await checkMemberURLs();

		showMembers = !showMembers;
	}

	async function addMembers(): Promise<void> {
		if (emails.length === 0) {
			alert('You must add at least 1 user');
			return;
		}

		try {
			const data = { method: 'add', user_ids: emails, sorted_ids: $sortedConvoMemberIDs };
			const response: Response = await fetch(
				`${clientSettings.apiBaseURL}/conversations/${$selectedConvoID}/update-members`,
				{
					method: 'PATCH',
					headers: {
						'Content-Type': 'application/json',
						Authorization: `Bearer ${token}`
					},
					body: JSON.stringify(data)
				}
			);

			if (!response.ok) {
				const errorResponse = await response.json();
				if (response.status === 404) {
					emailsErrorMsg = errorResponse.detail;
					input = '';
					return;
				} else {
					throw new Error();
				}
			}

			showModal = false;
			emails = [];
			input = '';
			emailsErrorMsg = '';
		} catch (error) {
			emailsErrorMsg = 'Error adding members. Please try again in a moment.';
		}
	}

	async function deleteUser(email: string): Promise<void> {
		try {
			const data = { method: 'remove', user_ids: [email], sorted_ids: $sortedConvoMemberIDs };
			const response: Response = await fetch(
				`${clientSettings.apiBaseURL}/conversations/${$selectedConvoID}/update-members`,
				{
					method: 'PATCH',
					headers: {
						'Content-Type': 'application/json',
						Authorization: `Bearer ${token}`
					},
					body: JSON.stringify(data)
				}
			);

			if (!response.ok) throw new Error();
		} catch (error) {
			websocketNotifStore.sendNotification(
				'There was an error removing the member. Please try again in a moment.'
			);
		}

		showModal = false;
		deleteConfirm = false;
		deleteEmail = '';
		leaveGroup = false;
		input = '';
	}

	function handleChangeChatName(): void {
		changeChatName.set(true);
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
				{#if deleteConfirm}
					<h1>Delete Member Confirmation</h1>
				{:else if leaveGroup}
					<h1>Leave Confirmation</h1>
				{:else}
					<h1>Add Members</h1>
				{/if}
			</div>

			{#if deleteConfirm}
				<div class="flex justify-center">Are you sure you want to remove {input}?</div>
				<div class="sm:flex sm:flex-row-reverse sm:px-6">
					<button
						on:click={() => deleteUser(deleteEmail)}
						class="inline-flex w-full justify-center rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:opacity-90 sm:ml-3 sm:w-auto"
						>Remove</button
					>
					<button
						on:click|preventDefault={closeModal}
						class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
						>Cancel</button
					>
				</div>
			{:else if leaveGroup}
				<div class="flex justify-center">Are you sure you want to leave?</div>
				<div class="sm:flex sm:flex-row-reverse sm:px-6">
					<button
						on:click={() => deleteUser($currUser.email)}
						class="inline-flex w-full justify-center rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:opacity-90 sm:ml-3 sm:w-auto"
						>Leave</button
					>
					<button
						on:click|preventDefault={closeModal}
						class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
						>Cancel</button
					>
				</div>
			{:else}
				<!-- Implicitly awaits the async function -->
				<form on:submit|preventDefault={addMembers}>
					<div class="flex flex-wrap items-center p-[5px] rounded gap-1">
						<!-- svelte-ignore a11y-autofocus -->
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
							type="text"
							autofocus
							class="flex-grow border-none outline-none p-[5px]"
							bind:value={input}
							on:keydown={handleInput}
							placeholder="User emails [Add with 'Enter' or 'Tab' or 'Comma']"
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
							disabled={emails.length === 0}
							class="inline-flex w-full justify-center rounded-md bg-blue-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:opacity-90 sm:ml-3 sm:w-auto disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:opacity-30"
							>Add Members</button
						>
						<button
							type="button"
							on:click|preventDefault={closeModal}
							class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
							>Cancel</button
						>
					</div>
				</form>
			{/if}
		</div>
	</div>
{/if}

{#if showCropModal}
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
				<h1>Change Photo</h1>
			</div>

			<div class="flex-1">
				<img
					bind:this={cropElement}
					src={cropUrl}
					alt="Crop this"
					class="max-w-full object-contain"
				/>
			</div>

			<hr class="border-t-gray-300 mt-2" />

			{#if isLoading}
				<div class="flex justify-center">
					<LoadingIcon size="w-7 h-7" />
				</div>
			{:else}
				<div class="flex flex-wrap items-center justify-end px-4 gap-3">
					<button
						on:click|preventDefault={closeCropModal}
						class="w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
						>Cancel</button
					>
					<button
						on:click|preventDefault={applyCrop}
						class="w-full justify-center rounded-md bg-blue-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:opacity-90 sm:w-auto"
						>Change</button
					>
				</div>
			{/if}
		</div>
	</div>
{/if}

<aside
	class="flex flex-col min-w-[180px] border-l border-l-black overflow-scroll min-h-screen md:min-w-[250px] min-[1120px]:min-w-[320px] bg-neutral-900 text-white"
>
	<div class="flex flex-col justify-center items-center mt-5 gap-3">
		{#if $selectedConvo?.presignedUrl}
			<img
				src={$selectedConvo?.presignedUrl}
				alt="The conversation's profile"
				class="w-[60px] md:w-[80px] overflow-hidden rounded-full"
			/>
		{:else}
			<!-- Group Chat Icon -->
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="1"
				stroke="currentColor"
				class="w-[60px] md:w-[80px] overflow-hidden"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z"
				/>
			</svg>
		{/if}
		<h1 class="font-bold text-base md:text-lg">{$selectedConvo?.convoName}</h1>
	</div>

	<div class="flex flex-col items-start mx-2 mt-8">
		<div
			class="flex flex-col justify-start md:flex-row md:justify-between flex-grow w-full md:items-center md:gap-2"
		>
			<button
				class="flex px-2 py-3 rounded-md flex-grow gap-2 hover:bg-neutral-800 text-start font-semibold text-sm md:text-base"
				on:click={getMembers}
				class:items-center={!showMembers}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5 transition-transform"
					class:rotate-90={showMembers}
				>
					<path
						fill-rule="evenodd"
						d="M8.22 5.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06-1.06L11.94 10 8.22 6.28a.75.75 0 0 1 0-1.06Z"
						clip-rule="evenodd"
					/>
				</svg>

				Members
			</button>
			<button
				class="gap-1 hover:text-neutral-300 text-sm items-center mr-2 h-fit hidden md:flex"
				on:click={openModal}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="w-4 h-4"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
				</svg>
				Add Member
			</button>
		</div>
		{#if showMembers}
			<ul class="flex flex-col gap-2 w-full my-2">
				{#each $sortedConvoMemberIDs as memberID}
					<li class="flex flex-grow items-center justify-between md:ml-1 md:mr-1 min-[1120px]:mr-3">
						<div class="flex items-center gap-2">
							<div class="w-[20px] md:w-[40px] overflow-hidden rounded-full flex-shrink-0">
								{#if $convoMembers[memberID]?.presigned_url}
									{#if memberID === $currUser.id}
										<img src={$currUser.presigned_url} alt="The user's avatar" />
									{:else}
										<img src={$convoMembers[memberID]?.presigned_url} alt="The user's avatar" />
									{/if}
								{:else}
									<svg
										xmlns="http://www.w3.org/2000/svg"
										fill="none"
										viewBox="0 0 24 24"
										stroke-width="1.1"
										stroke="currentColor"
										class="scale-110 text-neutral-200"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
										/>
									</svg>
								{/if}
							</div>

							<div class="flex-shrink-1 text-sm md:text-base">
								{$convoMembers[memberID]?.first_name}
								{$convoMembers[memberID]?.last_name}
							</div>
						</div>
						<!-- svelte-ignore a11y-click-events-have-key-events -->
						<!-- svelte-ignore a11y-no-static-element-interactions -->
						{#if memberID !== $currUser.id}
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke-width="1.5"
								stroke="currentColor"
								class="w-4 h-4 md:w-6 md:h-6 hover:cursor-pointer text-red-600 flex-shrink-0"
								on:click={() =>
									deleteConfirmation(
										// @ts-ignore
										$convoMembers[memberID]?.email,
										$convoMembers[memberID]?.first_name + ' ' + $convoMembers[memberID]?.last_name
									)}
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
								/>
							</svg>
						{:else}
							<p class="text-neutral-200 hidden md:flex">Me</p>
						{/if}
					</li>
				{/each}
			</ul>
		{/if}

		<button
			class="px-2 py-3 rounded-md flex-grow w-full hover:bg-neutral-800 text-center font-semibold flex justify-center text-sm md:hidden"
			on:click={openModal}
		>
			Add Member
		</button>

		<button
			class="px-2 py-3 rounded-md flex-grow w-full hover:bg-neutral-800 font-semibold flex justify-center md:justify-start text-center md:text-start text-sm md:text-base"
			on:click|stopPropagation={handleChangeChatName}
		>
			Change Chat Name
		</button>

		<label
			for="profilePhoto"
			class="px-2 py-3 rounded-md flex-grow w-full hover:bg-neutral-800 font-semibold flex justify-center md:justify-start text-center md:text-start text-sm md:text-base cursor-pointer"
		>
			Change Chat Photo
			<input
				id="profilePhoto"
				name="profilePhoto"
				type="file"
				accept=".jpg,.jpeg"
				class="hidden"
				on:change={onFileSelected}
			/>
		</label>
	</div>
	<div class="flex w-full mb-4 mt-auto">
		<button
			class="flex-grow text-center bg-red-600 hover:opacity-90 mx-3 rounded-md px-2 py-1 text-white"
			on:click={leaveConfirmation}
		>
			Leave Group
		</button>
	</div>
</aside>
