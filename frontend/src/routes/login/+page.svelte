<script lang="ts">
	export let form;
</script>

<div class="min-h-screen bg-black flex flex-col gap-20">
	<header class="bg-black text-white">
		<div class="max-w-[1440px] mx-auto px-[1rem] md:px-12 py-5">
			<nav class="px-6 py-4 flex items-center justify-between">
				<!-- Logo -->
				<div>
					<a href="/">
						<img src="/images/logo-white.svg" alt="Logo" class="h-12" />
					</a>
				</div>
			</nav>
		</div>
	</header>

	<div class="bg-black text-white flex flex-col justify-center items-center">
		<h1 class="text-3xl font-bold mb-3">Log In</h1>
		{#if form?.incorrect}
			<div class="border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
				<strong class="font-bold">Error:</strong>
				<span class="block sm:inline">Invalid email or password</span>
			</div>
		{:else if form?.error}
			<div class="border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
				<strong class="font-bold">Error:</strong>
				<span class="block sm:inline">{form.error}</span>
			</div>
		{/if}
		<form
			class="bg-gray-900 w-[25%] shadow-md rounded-xl px-8 pt-6 pb-8 mb-4"
			method="POST"
			action="?/login"
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

			<div class="mb-10">
				<label for="password" class="block text-sm font-bold mb-2"> Password </label>
				<input
					required
					type="password"
					name="password"
					id="password"
					class="shadow border rounded w-full py-2 px-3 leading-tight focus:outline-none text-black"
				/>
			</div>

			<div class="flex items-center justify-center mb-4">
				<button
					type="submit"
					class="font-bold py-2 px-4 rounded focus:outline-none bg-blue-700 hover:bg-blue-800 transition"
					>Log in</button
				>
			</div>

			<div class="flex items-center justify-center">
				<span class="text-sm text-gray-100">
					Don't have an account? <a href="/signup" class="hover:underline">
						<strong class="font-bold">Sign up</strong>
					</a>
				</span>
			</div>
		</form>
	</div>
</div>
