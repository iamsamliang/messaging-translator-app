<script lang="ts">
	import { convoMembers, selectedConvo } from '$lib/stores/stores';

	export let content: string;
	export let time: string;
	export let senderID: number;
	export let senderName: string | null;
	export let currUserID: number;
	export let displayPhoto: boolean;
</script>

{#if senderID !== currUserID}
	{#if $selectedConvo?.isGroupChat}
		<div class="flex items-end max-w-[80%] gap-2" class:mb-2={displayPhoto}>
			<!-- Profile picture -->
			<div class="w-[38px] overflow-hidden rounded-full flex-shrink-0">
				{#if displayPhoto}
					{#if $convoMembers[senderID]?.presigned_url}
						<img src={$convoMembers[senderID]?.presigned_url} alt="The user's avatar" />
					{:else}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="1.1"
							stroke="currentColor"
							class="scale-125"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
							/>
						</svg>
					{/if}
				{/if}
			</div>

			<!-- Sender Name and Text Message -->
			<div class="flex flex-col min-w-0">
				{#if senderName}
					<p class="text-xs text-gray-600 ml-[12px]">
						{senderName}
					</p>
				{/if}
				<div class="message max-w-full">
					<div class="message-content min-w-0">{content}</div>
					<div class="message-time">{time}</div>
				</div>
			</div>
		</div>
	{:else}
		<div class="message max-w-[80%]" class:mb-2={displayPhoto}>
			<div class="message-content min-w-0">{content}</div>
			<div class="message-time">{time}</div>
		</div>
	{/if}
{:else}
	<div class="message from-curr-user max-w-[80%]" class:mb-2={displayPhoto}>
		<div class="message-content min-w-0">{content}</div>
		<div class="message-time">{time}</div>
	</div>
{/if}

<style>
	.message {
		display: flex;
		/* Set the max width for each message */
		min-width: 0;
		/* This ensures that the width can shrink below content size if needed */
		word-wrap: break-word;
		overflow-wrap: break-word;
		/* This will wrap long words onto the next line */
		padding: 7px;
		background-color: #fff;
		/* White background for messages */
		border-radius: 15px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		/* Soft shadow for messages */
		align-self: flex-start;
		/* Aligns messages to the start of the flex container */
	}

	.from-curr-user {
		align-self: flex-end;
		background-color: rgb(0, 102, 255);
		color: #fff;
	}

	.message-content {
		margin-left: 5px;
		margin-right: 6px;
	}

	.message-time {
		color: #b9b9b9;
		font-size: 0.8rem;
		margin-right: 5px;
		display: flex;
		flex-grow: 1;
		flex-direction: column;
		justify-content: flex-end;
	}
</style>
