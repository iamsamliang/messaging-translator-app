<script lang="ts">
	import { createEventDispatcher, type EventDispatcher } from 'svelte';

	export let chatName: string;
	export let isSelected: boolean;
	export let id: string;

	const dispatch: EventDispatcher<any> = createEventDispatcher();

	function handleClick(): void {
		dispatch('click');
	}
</script>

<li class="chat rounded-lg" class:is-selected={isSelected} {id}>
	<button type="button" on:click={handleClick} aria-label={`Select conversation with ${chatName}`}>
		<div class="chat-photo">
			<img src="/images/profile_photo.png" alt="The user's avatar" />
		</div>
		<div class="chat-info">
			<div class="chat-name overflow-hidden text-ellipsis">{chatName}</div>
			<div class="last-message" class:is-selected-color={isSelected}>Say Hello to Alice</div>
		</div>
		<div class="message-info">
			<div class="last-message-time" class:is-selected-color={isSelected}>18:23</div>
			<div class="unread-indicator"></div>
		</div>
	</button>
</li>

<style>
	/* Style each chat item */
	.chat {
		display: flex;
		align-items: center;
		padding: 0.5rem 1rem;
		border-bottom: 1px solid #ccc;
		height: 80px;
		/* Separator between chats */
	}

	.chat button {
		all: unset;
		display: flex;
		align-items: center;
		height: 100%;
		width: 100%;
	}

	/* Style the avatar image */
	.chat-photo {
		flex: 0 0 auto;
		height: 100%;
		border-radius: 50%;
		/* Circular shape */
		overflow: hidden;
		/* Ensures the image doesn't overflow the circular shape */
		margin-right: 10px;
		/* Space between avatar and text */
	}

	/* The image inside the avatar div */
	.chat-photo img {
		height: 100%;
		object-fit: cover;
	}

	/* Style the chat's name and last message */
	.chat-info {
		height: 100%;
		display: flex;
		flex-direction: column;
		justify-content: flex-start;
		/* flex-grow: 1; */
		font-size: 1.06rem;
		gap: 2px;
		/* Allows the text to take up the available space */
		flex: 1; /* Start with zero width before growing */
		min-width: 0;
		margin-right: 5px;
	}

	.chat-name {
		font-weight: bold;
		/* Make the name stand out */
	}

	.last-message {
		color: #666;
		/* A lighter color for the last message */
		font-size: 0.9em;
		/* A smaller font size */
	}

	.message-info {
		flex: 0 0 auto;
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		align-items: flex-end;
		height: 100%;
	}

	/* Style the timestamp */
	.last-message-time {
		color: #666;
	}

	/* Unread message indicator */
	.unread-indicator {
		background-color: #007bff;
		/* Blue background for the indicator */
		color: white;
		/* White text color */
		border-radius: 50%;
		/* Circular shape */
		/* padding: 5px; */
		/* Padding inside the indicator */
		display: flex;
		/* To center the content */
		align-items: center;
		/* Center content vertically */
		justify-content: center;
		/* Center content horizontally */
		width: 0.6rem;
		/* Fixed width */
		height: 0.6rem;
		/* Fixed height */
	}

	.is-selected {
		background-color: #007bff;
		color: white;
	}

	.is-selected-color {
		color: white;
	}
</style>
