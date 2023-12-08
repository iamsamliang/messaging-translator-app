<!-- Sidebar for contacts -->
<aside class="contacts-sidebar">
	<!-- Sidebar Header -->
	<header class="contacts-sidebar-header">
		<!-- Search bar -->
		<div class="contacts-search-bar">
			<input type="text" placeholder="Search..." />
		</div>

		<!-- Create new chat button -->
		<div class="create-chat-btn-container">
			<button class="create-chat-btn" aria-label="New chat">+</button>
		</div>
		<!-- Using a plus sign for simplicity -->
	</header>

	<!-- Contact list -->
	<ul class="contact-list">
		<!-- Individual Contact 1 -->
		<li class="contact">
			<div class="contact-photo">
				<img src="/images/profile_photo.png" alt="The user's avatar" />
			</div>
			<div class="contact-info">
				<div class="contact-name">Robert</div>
				<div class="last-message">Say Hello to Alice</div>
			</div>
			<div class="message-info">
				<div class="last-message-time">18:23</div>
				<div class="unread-indicator">2</div>
			</div>
		</li>
		<!-- Individual Contact 2 -->
		<!-- .................... -->
		<!-- Individual Contact N -->
	</ul>
</aside>

<style>
	/* Set up the sidebar with a background color, text color, and padding */
	.contacts-sidebar {
		width: 25%;
		border-right: 1px solid #ccc;
	}

	/* Style the sidebar header to display its children inline */
	.contacts-sidebar-header {
		display: flex;
		/* Use flexbox for layout */
		/* justify-content: space-between; */
		/* Space out the search bar and new chat button */
		align-items: center;
		/* Vertically center items in the header */

		padding-top: 1rem;
		padding-bottom: 0.2rem;
	}

	/* Style the search container for the input and search button */
	.contacts-search-bar {
		display: flex;
		/* Align the search input and button inline */
		padding-left: 1rem;
		width: 80%;
		/* Allow the search container to fill the space */
	}

	/* Style the search input field */
	.contacts-search-bar input[type='text'] {
		width: 100%;
		/* Full width of the container */
		padding: 0.5rem;
		/* Padding inside the input field */
		border: 1px solid #333;
		/* Border to make it stand out */
		border-radius: 4px;
		/* Rounded corners */
	}

	.create-chat-btn-container {
		display: flex;
		justify-content: center;
		/* Aligns the button to the right */
		width: 20%;
		/* Takes the full width of its parent */
	}

	.contacts-search-bar,
	.create-chat-btn-container {
		height: 36px;
	}

	/* Style the create chat button */
	.create-chat-btn {
		/* display: flex; */
		flex-grow: 0.3;
		align-items: center;
		justify-content: center;
		/* padding: 1rem; */
		/* Padding inside the button */

		border: none;
		/* No border */
		border-radius: 20px;
		/* Rounded pill shape */
		cursor: pointer;
		/* Pointer cursor on hover */
		font-size: 1.5rem;
		/* Larger font size for the plus icon */
		/* width: 30%; */

		/* padding: 10px 20px; */
		/* equal top/bottom and left/right padding */
		/* line-height: 1; */

		background-color: #007bff;
		/* example background color */
	}

	/* Add a hover effect for buttons */
	button:hover {
		opacity: 0.9;
		/* Slightly transparent on hover */
	}

	/* Reset list styles and add padding */
	.contact-list {
		list-style-type: none;
		padding: 0;
		margin: 0;
	}

	/* Style each contact item */
	.contact {
		display: flex;
		align-items: center;
		padding: 0.5rem 1rem;
		border-bottom: 1px solid #ccc;
		height: 80px;
		/* Separator between contacts */
	}

	/* Style the avatar image */
	.contact-photo {
		height: 100%;
		border-radius: 50%;
		/* Circular shape */
		overflow: hidden;
		/* Ensures the image doesn't overflow the circular shape */
		margin-right: 10px;
		/* Space between avatar and text */
	}

	/* The image inside the avatar div */
	.contact-photo img {
		width: auto;
		height: 100%;
		min-width: 100%;
		object-fit: cover;
	}

	/* Style the contact's name and last message */
	.contact-info {
		height: 100%;
		display: flex;
		flex-direction: column;
		justify-content: flex-start;
		flex-grow: 1;
		font-size: 1.06rem;
		gap: 2px;
		/* Allows the text to take up the available space */
	}

	.contact-name {
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
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		align-items: end;
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
		font-size: 1rem;
		/* Smaller font size */
		display: flex;
		/* To center the content */
		align-items: center;
		/* Center content vertically */
		justify-content: center;
		/* Center content horizontally */
		width: 1.4rem;
		/* Fixed width */
		height: 1.4rem;
		/* Fixed height */
		min-width: 1.4rem;
		/* Ensure it doesn't shrink smaller than content */
	}
</style>
