<script lang="ts">
	export let content: string;
	export let time: string;
	export let fromCurrUser: boolean;
</script>

<div class="message" class:from-curr-user={fromCurrUser}>
	<div class="message-content">{content}</div>
	<div class="message-time">{time}</div>
</div>

<style>
	.message {
		display: flex;
		max-width: 60%;
		/* Set the max width for each message */
		min-width: 0;
		/* This ensures that the width can shrink below content size if needed */
		word-wrap: break-word;
		/* This will wrap long words onto the next line */
		margin-bottom: 10px;
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
		margin-right: 10px;
	}

	.message-time {
		color: #b9b9b9;
		font-size: 0.8rem;
		margin-right: 5px;
		height: 100%;
		display: flex;
		flex-grow: 1;
		flex-direction: column;
		justify-content: flex-end;
	}
</style>
