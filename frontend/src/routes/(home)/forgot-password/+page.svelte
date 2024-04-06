<script lang="ts">
	import { enhance } from '$app/forms';
	import type { SubmitFunction } from '@sveltejs/kit';
	import toast, { Toaster } from 'svelte-french-toast';
	import LoadingIcon from '$lib/components/LoadingIcon.svelte';
	import Unverified from './Unverified.svelte';
	import { onMount } from 'svelte';
	import clientSettings from '$lib/config/config.client';
	import { loadCaptcha } from '$lib/captcha';
	export let form;

	let loading = false;

	const submitResetPassword: SubmitFunction = () => {
		loading = true;

		return async ({ result, update }) => {
			switch (result.type) {
				case 'success':
					toast.success(`${result.data?.message}`, {
						duration: 5000
					});
					break;
				case 'failure':
					if (result.data?.unverified) {
						toast(Unverified, {
							duration: 10000
						});
					} else if (result.data?.genErrors) {
						toast.error(`${result.data?.genErrors}`, {
							duration: 5000
						});
					}
					break;
				default:
					break;
			}

			loading = false;
			await update();
		};
	};

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

<Toaster />

<div class="bg-black text-white flex flex-col justify-center items-center mt-5">
	<h1 class="text-3xl font-bold mb-2">Forgot Password?</h1>
	<p class="mb-8 text-sm text-gray-400">
		No worries, we'll email you a link to reset your password.
	</p>

	<form
		class="bg-gray-900 w-[85%] min-[450px]:w-[25rem] shadow-md rounded-xl px-8 py-6 mb-5"
		method="POST"
		action="?/sendEmail"
		use:enhance={submitResetPassword}
	>
		<div class="mb-5">
			<label for="email" class="block text-sm font-bold mb-2"> Email </label>
			<input
				required
				type="text"
				name="email"
				id="email"
				class="shadow border rounded w-full py-2 px-3 leading-tight focus:outline-none text-black"
				value={form?.data?.email ?? ''}
			/>
			{#if form?.fieldErrors?.email}
				<label for="email" class="block text-sm text-red-500 mt-2">
					{form.fieldErrors.email[0]}
				</label>
			{/if}
		</div>

		<div class="flex flex-col justify-center items-center mb-8">
			<div id="recaptcha-div" class="scale-75 min-[500px]:scale-90"></div>
			{#if form?.fieldErrors?.['g-recaptcha-response']}
				<label for="g-recaptcha-response" class="flex text-sm text-red-500 mt-2">
					{form.fieldErrors['g-recaptcha-response'][0]}
				</label>
			{/if}
		</div>

		<div class="flex items-center justify-center">
			{#if loading}
				<LoadingIcon size="w-7 h-7" />
			{:else}
				<button
					type="submit"
					class="font-bold py-2 px-4 rounded focus:outline-none bg-blue-700 hover:bg-blue-800 transition"
					>Reset password</button
				>
			{/if}
		</div>
	</form>

	<div class="flex items-center justify-center">
		<a href="/login" class="text-sm font-medium inline-flex items-center gap-2 hover:underline"
			><svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="1.8"
				stroke="currentColor"
				class="w-4 h-4"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M9 15 3 9m0 0 6-6M3 9h12a6 6 0 0 1 0 12h-3"
				/>
			</svg>
			Back to log in</a
		>
	</div>
</div>
