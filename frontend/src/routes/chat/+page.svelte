<script lang="ts">
	import ChatHeader from './ChatHeader.svelte';
	import ChatInput from './ChatInput.svelte';
	import ContactsSidebar from './ContactsSidebar.svelte';
	import MessagesContainer from './MessagesContainer.svelte';
</script>

<main class="messaging-app">
	<ContactsSidebar />

	<!-- Actual Chat Area -->
	<section class="chat-area">
		<ChatHeader chatName="Robert" />
		<MessagesContainer />
		<ChatInput />

		<!-- Individual Chat Content for Group Chats-->
		<!-- <div class="message-container">
            <div class="message">
                <div class="message-sender-photo"></div>
                <div class="message-sender-name"></div>
                <div class="message-content"></div>
                <div class="message-time"></div>
            </div>
        </div> -->
	</section>
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
		width: 75%;
		/* Set a fixed width for the chat area or adjust as needed */
		height: 100vh;
		border-left: 1px solid #ccc;
		/* Border to separate from the rest of the interface */
	}
</style>
