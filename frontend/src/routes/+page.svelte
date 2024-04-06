<script lang="ts">
	import { languages } from '$lib/languages.js';
	import { onDestroy, onMount } from 'svelte';

	export let data;

	let isHamDropdown = false;

	function openHamDropdown() {
		isHamDropdown = true;
	}

	function closeHamdropdown() {
		isHamDropdown = false;
	}

	// Typing Animation
	let currentLangIndex = 0;
	let currentCharIndex = 0;
	let language = '';
	let languageFixed: string = languages[0];
	let langSpanOne: HTMLSpanElement;
	let langSpanTwo: HTMLSpanElement;
	let fadeDurationMS = 400; // ms
	let typeTimeout: NodeJS.Timeout;
	let deleteTimeout: NodeJS.Timeout;
	let fadeTimeout: NodeJS.Timeout;

	function typeLanguage() {
		if (currentCharIndex < languages[currentLangIndex].length) {
			language = languages[currentLangIndex].substring(0, currentCharIndex + 1);
			currentCharIndex++;
			typeTimeout = setTimeout(typeLanguage, 100); // Delay in milliseconds between characters
		} else {
			deleteTimeout = setTimeout(deleteLanguage, 2000); // Wait before starting to delete
		}
	}

	function deleteLanguage() {
		if (currentCharIndex > 0) {
			language = languages[currentLangIndex].substring(0, currentCharIndex - 1);
			currentCharIndex--;
			deleteTimeout = setTimeout(deleteLanguage, 75); // Faster deletion speed
		} else {
			currentLangIndex = (currentLangIndex + 1) % languages.length; // Loop back to start
			// Start fade out
			langSpanOne.classList.remove('fade-in');
			langSpanTwo.classList.remove('fade-in');

			fadeTimeout = setTimeout(() => {
				// Start fade in
				languageFixed = languages[currentLangIndex];
				langSpanOne.classList.add('fade-in');
				langSpanTwo.classList.add('fade-in');
			}, fadeDurationMS); // This timeout should match the CSS transition duration

			typeTimeout = setTimeout(typeLanguage, 750); // Delay before typing next language
		}
	}

	onMount(typeLanguage);

	onDestroy(() => {
		clearTimeout(typeTimeout);
		clearTimeout(deleteTimeout);
		clearTimeout(fadeTimeout);
	});
</script>

<div
	class="min-h-screen bg-black flex flex-col bg-gradient-to-b from-neutral-950 via-black via-80% to-gray-950"
>
	<!-- Header -->
	<header class="text-white sticky top-0 z-50">
		<div class="px-4 md:px-8 lg:px-20 py-5">
			<nav class="px-6 py-4 flex items-center justify-between">
				<!-- Logo -->
				<div>
					<a href="/">
						<img
							src="/images/logo-white.svg"
							alt="Logo"
							class="h-8 min-[378px]:h-10 min-[450px]:h-12"
						/>
					</a>
				</div>
				<!-- w-auto gap-x-[40px] hidden lg:flex justify-between items-center font-normal text-base text-blue-100 -->
				<!-- Nav Buttons for Larger Devices -->
				<div class="w-auto gap-x-[40px] items-center justify-between hidden sm:flex">
					{#if data.user}
						<a
							href="/chat"
							class="font-semibold border-none cursor-pointer text-white hover:text-blue-100 transition"
						>
							Your Chats
						</a>
						<form method="POST" action="?/logout">
							<button class="bg-gray-800 px-6 py-2 rounded-full hover:bg-gray-700 transition"
								>Log out</button
							>
						</form>
					{:else}
						<!-- text-base font-semibold border-none hover:underline cursor-pointer text-blue-100 hover:text-blue-100 text-white hover:text-white -->
						<a
							href="/signup"
							class="font-semibold border-none cursor-pointer text-white hover:text-blue-100 transition"
						>
							Sign up
						</a>
						<a
							href="/login"
							class="bg-gray-800 px-6 py-2 rounded-full hover:bg-gray-700 transition"
						>
							Log in
						</a>
					{/if}
				</div>

				<!-- Hamburger Icon For Mobile -->
				<!-- svelte-ignore a11y-click-events-have-key-events -->
				<!-- svelte-ignore a11y-no-static-element-interactions -->
				<div class="sm:hidden items-center" on:click={openHamDropdown}>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.1"
						stroke="currentColor"
						class="w-8 h-8 min-[378px]:w-9 min-[378px]:h-9 min-[450px]:w-10 min-[450px]:h-10"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
						/>
					</svg>
				</div>
			</nav>
		</div>
	</header>

	<!-- Landing Page -->
	<section class="w-full h-full flex flex-col justify-between items-center">
		<div class="flex flex-1 flex-col pt-8 px-8 md:px-12 lg:pl-28 w-full mr-auto">
			<div
				class="uppercase mb-3 lg:mb-4 text-base text-gray-200 flex text-center min-[500px]:text-start justify-center min-[500px]:justify-start"
			>
				<h1 class="uppercase mb-3 lg:mb-4 text-base text-gray-200">Break the Language Barrier</h1>
			</div>

			<div
				class="font-medium text-white text-[2.25rem] md:text-[68px] mb-8 md:mb-14 text-center min-[500px]:text-start"
			>
				<span>Chat With Anyone in</span>&nbsp;<span class="text-green-600">{language}</span>
				<!-- <span class="border-l border-l-green-600 ml-2 animate-blink h-[60px] self-center"></span> -->
			</div>

			<div class="text-lg text-gray-200 mb-20 flex text-center min-[500px]:text-start">
				<p>
					Pick <span class="fade-effect fade-in" bind:this={langSpanOne}>{languageFixed}</span>
					as your language, and we will translate any messages sent your way to
					<span class="fade-effect fade-in" bind:this={langSpanTwo}>{languageFixed}</span>.
				</p>
			</div>
			<div class="flex justify-center min-[500px]:justify-start">
				<a
					href="/login"
					class="text-lg bg-white font-semibold px-6 py-4 rounded-full hover:bg-blue-200 transition"
				>
					{#if data.user}
						Chat Now, {data.user.first_name}
					{:else}
						Start Chatting Now
					{/if}
				</a>
			</div>
		</div>
	</section>

	<!-- Footer -->
	<footer class="mt-auto">
		<div class="flex flex-col justify-center items-center mb-5 gap-1">
			<span class="text-white">&copy; Sam Liang</span>
			<span class="text-white text-xs">For code inquries, iamsamliang8@gmail.com</span>
		</div>
	</footer>

	<!-- Pop Up Menu from Hamburger Icon -->
	<div
		class="fixed bg-neutral-800 w-full text-white flex justify-center items-center text-[25px] font-semibold tracking-[1px] z-50 overflow-hidden origin-bottom duration-500"
		class:h-0={!isHamDropdown}
		class:h-screen={isHamDropdown}
	>
		<ul class="space-y-3 flex flex-col justify-center items-center">
			{#if data.user}
				<li class="hover:-translate-y-[5px] transition">
					<a href="/chat" class="border-none cursor-pointer hover:text-blue-200 transition">
						Your Chats
					</a>
				</li>
				<li class="hover:-translate-y-[5px] transition">
					<form method="POST" action="?/logout">
						<button class="border-none cursor-pointer hover:text-blue-200 transition"
							>Log out</button
						>
					</form>
				</li>
			{:else}
				<li class="hover:-translate-y-[5px] transition">
					<a href="/signup" class="border-none cursor-pointer hover:text-blue-200 transition">
						Sign up
					</a>
				</li>
				<li class="hover:-translate-y-[5px] transition">
					<a href="/login" class="border-none cursor-pointer hover:text-blue-200 transition">
						Log in
					</a>
				</li>
			{/if}
		</ul>

		<!-- Close Button -->
		<!-- svelte-ignore a11y-click-events-have-key-events -->
		<!-- svelte-ignore a11y-no-static-element-interactions -->
		<div class="absolute top-8 right-8 cursor-pointer" on:click={closeHamdropdown}>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="1.1"
				stroke="currentColor"
				class="w-10 h-10"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
			</svg>
		</div>
	</div>
</div>

<style>
	.fade-effect {
		transition: opacity 400ms linear;
		opacity: 0;
	}

	.fade-in {
		opacity: 1 !important;
	}
</style>
