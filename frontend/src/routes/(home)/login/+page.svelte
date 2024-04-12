<script lang="ts">
	import { enhance } from '$app/forms';
	import { goto } from '$app/navigation';
	import clientSettings from '$lib/config/config.client';

	let loginForm: HTMLFormElement;
	let incorrect: boolean = false;
	let unverified: boolean = false;
	let errorMsg: string = '';

	async function handleLogin() {
		incorrect = false;
		unverified = false;
		errorMsg = '';
		const formData = new FormData(loginForm);

		try {
			const response: Response = await fetch(`${clientSettings.apiBaseURL}/login/access-token`, {
				method: 'POST',
				body: formData,
				credentials: 'include'
			});

			if (!response.ok) {
				const errorResponse = await response.json();

				if (response.status === 401) {
					incorrect = true;
					return;
				} else if (response.status === 412) {
					unverified = true;
					return;
				}
				throw new Error(errorResponse.detail);
			}
		} catch (error) {
			if (error instanceof Error) {
				errorMsg = error.message;
			}

			// Handle other cases, defaulting to a generic message
			errorMsg = 'An unknown error occurred';
			return;
		}

		goto('/chat');
	}
</script>

<div class="bg-black text-white flex flex-col justify-center items-center mt-5">
	<h1 class="text-3xl font-bold mb-3">Log In</h1>
	{#if incorrect}
		<div class="border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
			<strong class="font-bold">Error:</strong>
			<span class="block sm:inline">Invalid email or password</span>
		</div>
	{:else if unverified}
		<div class="border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
			<strong class="font-bold">Error:</strong>
			<span class="block sm:inline"
				>Unverified account. To resend verification email, <a
					data-sveltekit-preload-data="tap"
					href="/resend-email"
					class="underline underline-offset-2 hover:text-white">click here</a
				></span
			>
		</div>
	{:else if errorMsg}
		<div class="border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
			<strong class="font-bold">Error:</strong>
			<span class="block sm:inline">{errorMsg}</span>
		</div>
	{/if}
	<form
		class="bg-gray-900 w-[85%] min-[450px]:w-[25rem] shadow-md rounded-xl px-8 py-6 mb-5"
		on:submit|preventDefault={handleLogin}
		use:enhance
		bind:this={loginForm}
	>
		<div class="mb-4">
			<label for="email" class="block text-sm font-bold mb-2"> Email </label>
			<input
				required
				type="email"
				name="username"
				id="email"
				class="shadow border rounded w-full py-2 px-3 leading-tight focus:outline-none text-black"
			/>
		</div>

		<div class="mb-6">
			<label for="password" class="block text-sm font-bold mb-2"> Password </label>
			<input
				required
				type="password"
				name="password"
				id="password"
				class="shadow border rounded w-full py-2 px-3 leading-tight focus:outline-none text-black"
			/>
		</div>

		<div class="flex items-center justify-center">
			<button
				type="submit"
				class="font-bold py-2 px-4 rounded focus:outline-none bg-blue-700 hover:bg-blue-800 transition"
				>Log in</button
			>
		</div>
	</form>

	<div class="flex items-center justify-center">
		<span class="text-sm text-gray-100">
			Don't have an account? <a href="/signup" class="hover:underline">
				<strong class="font-bold">Sign up</strong>
			</a>
		</span>
	</div>

	<div class="flex items-center justify-center mt-2">
		<a href="/forgot-password" class="text-sm text-gray-100 hover:underline">
			<strong class="font-bold">Forgot Password?</strong>
		</a>
	</div>
</div>
