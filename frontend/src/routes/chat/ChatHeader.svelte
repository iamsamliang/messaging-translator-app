<script lang="ts">
	// get the chat photo from the backend

	import { selectedConvo } from '$lib/stores/stores';
</script>

<!-- Individual Chat Header -->
{#if $selectedConvo}
	<header class="chat-header">
		<div class="chat-photo-name-container">
			<div class="chat-photo">
				<img src="/images/profile_photo.png" alt="The user's avatar" />
			</div>
			<div class="chat-name">{$selectedConvo.conversation_name}</div>
		</div>
		<div class="chat-options"></div>
	</header>
{/if}

<style>
	.chat-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 10px;
		background-color: #f7f7f7;
		border-bottom: 1px solid #ccc;
	}

	.chat-photo-name-container {
		display: flex;
		align-items: center;
	}

	.chat-photo {
		width: 40px;
		height: 40px;
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
	/* 
    .chat-name-status {
        flex-grow: 1;
        padding-left: 10px;
    } */

	.chat-name {
		font-weight: bold;
	}
</style>
