<script lang="ts">
	import { enhance } from '$app/forms';
	import { loadCaptcha } from '$lib/captcha.js';
	import clientSettings from '$lib/config/config.client.js';
	import { languages } from '$lib/languages.js';
	import { onMount } from 'svelte';

	export let form;

	onMount(() => {
		// @ts-expect-error
		window.onloadCallback = function () {
			// @ts-expect-error
			grecaptcha.render('recaptcha-div', {
				sitekey: clientSettings.reCaptchaSiteKey
			});
		};

		loadCaptcha(`onloadCallback`);
	});
</script>

<div class="bg-black text-white flex flex-col justify-center items-center">
	<h1 class="text-3xl font-bold mb-3">Register</h1>
	{#if form?.message}
		<div class="border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
			<strong class="font-bold">Error:</strong>
			<span class="block sm:inline">{form.message}</span>
		</div>
	{/if}
	<form
		class="bg-gray-900 shadow-md rounded-xl px-8 pt-5 pb-4 mb-4 w-[85%] min-[450px]:w-[25rem] md:w-[30rem] lg:w-[35rem]"
		method="POST"
		action="?/create"
		use:enhance
	>
		<div class="mb-4">
			<label for="firstname" class="block text-sm font-bold mb-2"> First Name </label>
			<input
				type="text"
				name="firstName"
				id="firstname"
				maxlength="100"
				class="shadow border rounded w-full py-[6px] px-3 leading-tight focus:outline-none text-black"
				value={form?.data?.firstName ?? ''}
			/>
			{#if form?.fieldErrors?.firstName}
				<label for="firstname" class="block text-sm text-red-500 mt-2">
					{form.fieldErrors.firstName[0]}
				</label>
			{/if}
		</div>

		<div class="mb-4">
			<label for="lastname" class="block text-sm font-bold mb-2"> Last Name </label>
			<input
				type="text"
				name="lastName"
				id="lastname"
				maxlength="100"
				class="shadow border rounded w-full py-[6px] px-3 leading-tight focus:outline-none text-black"
				value={form?.data?.lastName ?? ''}
			/>
			{#if form?.fieldErrors?.lastName}
				<label for="lastname" class="block text-sm text-red-500 mt-2">
					{form.fieldErrors.lastName[0]}
				</label>
			{/if}
		</div>

		<div class="mb-4">
			<label for="email" class="block text-sm font-bold mb-2"> Email </label>
			<input
				type="email"
				name="email"
				id="email"
				class="shadow border rounded w-full py-[6px] px-3 leading-tight focus:outline-none text-black"
				value={form?.data?.email ?? ''}
			/>
			{#if form?.fieldErrors?.email}
				<label for="email" class="block text-sm text-red-500 mt-2">
					{form.fieldErrors.email[0]}
				</label>
			{/if}
		</div>

		<div class="mb-4">
			<label for="password" class="block text-sm font-bold mb-2"> Password </label>
			<input
				type="password"
				name="password"
				id="password"
				class="shadow border rounded w-full py-[6px] px-3 leading-tight focus:outline-none text-black"
			/>
			{#if form?.fieldErrors?.password}
				<label for="password" class="block text-sm text-red-500 mt-2">
					{form.fieldErrors.password[0]}
				</label>
			{/if}
		</div>

		<div class="mb-4">
			<label for="confPassword" class="block text-sm font-bold mb-2"> Confirm Password </label>
			<input
				type="password"
				name="confPassword"
				id="confPassword"
				class="shadow border rounded w-full py-[6px] px-3 leading-tight focus:outline-none text-black"
			/>
			{#if form?.fieldErrors?.confPassword}
				<label for="confPassword" class="block text-sm text-red-500 mt-2">
					{form.fieldErrors.confPassword[0]}
				</label>
			{/if}
		</div>

		<div class="mb-3 space-y-2">
			<label for="language" class="block text-sm font-bold"> Language </label>
			<select
				id="language"
				name="language"
				class="border border-gray-500 rounded-sm w-full focus:outline-none text-black pl-1 py-1"
				value={form?.data?.language ?? languages[0]}
			>
				{#each languages as language}
					<option value={language}>{language}</option>
				{/each}
			</select>
			<p class="text-[0.8rem] text-gray-400">
				Messages sent to you will be translated to this language.
			</p>
			{#if form?.fieldErrors?.language}
				<label for="language" class="block text-sm text-red-500 mt-2">
					{form.fieldErrors.language[0]}
				</label>
			{/if}
		</div>

		<!-- <div class="mb-4">
				<label for="language" class="block text-sm font-bold mb-2"> Default Language </label>
				<input
					type="string"
					name="language"
					id="language"
					class="shadow border rounded w-full py-[6px] px-3 leading-tight focus:outline-none text-black"
				/>
			</div> -->

		<div class="mb-6">
			<label for="apiKey" class="block text-sm font-bold mb-2"> OpenAI API Key </label>
			<input
				type="text"
				name="apiKey"
				id="apiKey"
				class="shadow border rounded w-full py-[6px] px-3 leading-tight focus:outline-none text-black"
			/>
			{#if form?.fieldErrors?.apiKey}
				<label for="apiKey" class="block text-sm text-red-500 mt-2">
					{form.fieldErrors.apiKey[0]}
				</label>
			{/if}
		</div>

		<div class="flex flex-col justify-center items-center mb-4">
			<div id="recaptcha-div" class="scale-75 min-[500px]:scale-100"></div>
			{#if form?.fieldErrors?.['g-recaptcha-response']}
				<label for="g-recaptcha-response" class="flex text-sm text-red-500 mt-2">
					{form.fieldErrors['g-recaptcha-response'][0]}
				</label>
			{/if}
		</div>

		<div class="flex items-center justify-center mb-4">
			<button
				type="submit"
				class="font-bold py-2 px-4 rounded focus:outline-none bg-blue-700 hover:bg-blue-800 transition"
				>Register</button
			>
		</div>

		<div class="flex items-center justify-center">
			<span class="text-sm text-gray-100"
				>Already have an account? <a href="/login" class="hover:underline"
					><strong class="font-bold">Log in</strong></a
				></span
			>
		</div>
	</form>
</div>
