<script lang="ts">
	import { enhance } from '$app/forms';
	import { goto } from '$app/navigation';
	import { loadCaptcha } from '$lib/captcha.js';
	import LoadingIcon from '$lib/components/LoadingIcon.svelte';
	import clientSettings from '$lib/config/config.client.js';
	import type { SubmitFunction } from '@sveltejs/kit';
	import { onMount } from 'svelte';
	import toast, { Toaster } from 'svelte-french-toast';

	export let form;
	export let data;

	let loading = false;

	async function sleep(ms: number) {
		return new Promise((resolve) => setTimeout(resolve, ms));
	}

	const submitNewPassword: SubmitFunction = () => {
		loading = true;

		return async ({ result, update }) => {
			switch (result.type) {
				case 'redirect':
					break;
				case 'error':
					break;
				case 'success':
					loading = false;
					const waitDuration = 4000; // ms

					await toast.promise(sleep(waitDuration), {
						loading: `Password changed. Going to LOGIN PAGE in ${waitDuration / 1000} seconds`,
						success: 'Redirecting...',
						error: 'Redirecting failed.'
					});
					await sleep(1000);

					await goto('/login');
				case 'failure':
					if (result.data?.genErrors) {
						toast.error(`${result.data?.genErrors}`, {
							duration: 2000
						});
					}
					loading = false;
					await update();
					break;
			}
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

<div class="text-white flex flex-col justify-center items-center">
	<h1 class="text-3xl font-bold mb-5">Reset Password</h1>
	<form
		class="bg-gray-900 w-[85%] min-[450px]:w-[25rem] shadow-md rounded-xl px-8 py-6 mb-5"
		method="POST"
		action="?/resetPassword"
		use:enhance={submitNewPassword}
	>
		<div class="mb-4">
			<label for="password" class="block text-sm font-bold mb-2"> New Password </label>
			<input
				required
				type="password"
				name="password"
				id="password"
				class="shadow border rounded w-full py-2 px-3 leading-tight focus:outline-none text-black"
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
				required
				type="password"
				name="confPassword"
				id="confPassword"
				class="shadow border rounded w-full py-2 px-3 leading-tight focus:outline-none text-black"
			/>
			{#if form?.fieldErrors?.confPassword}
				<label for="confPassword" class="block text-sm text-red-500 mt-2">
					{form.fieldErrors.confPassword[0]}
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
		<input hidden type="text" name="token" value={data.token ?? ''} />

		<div class="flex items-center justify-center">
			{#if loading}
				<LoadingIcon size="w-7 h-7" />
			{:else}
				<button
					type="submit"
					class="text-base font-bold py-2 px-4 rounded focus:outline-none bg-blue-700 hover:bg-blue-800 transition"
					>Confirm</button
				>
			{/if}
		</div>
	</form>
</div>
