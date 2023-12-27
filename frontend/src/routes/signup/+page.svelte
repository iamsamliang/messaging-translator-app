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
		<h1 class="text-3xl font-bold mb-3">Register</h1>
		{#if form?.error}
			<div class="border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
				<strong class="font-bold">Error!</strong>
				<span class="block sm:inline">{form.error}</span>
			</div>
		{/if}
		<form
			class="bg-gray-900 shadow-md rounded-xl px-8 pt-6 pb-8 mb-4 w-[30%]"
			method="POST"
			action="?/create"
		>
			<div class="mb-4">
				<label for="firstname" class="block text-sm font-bold mb-2"> First Name </label>
				<input
					required
					type="text"
					name="firstName"
					id="firstname"
					class="shadow border rounded w-full py-2 px-3 leading-tight focus:outline-none text-black"
				/>
			</div>

			<div class="mb-4">
				<label for="lastname" class="block text-sm font-bold mb-2"> Last Name </label>
				<input
					required
					type="text"
					name="lastName"
					id="lastname"
					class="shadow border rounded w-full py-2 px-3 leading-tight focus:outline-none text-black"
				/>
			</div>

			<div class="mb-4">
				<label for="email" class="block text-sm font-bold mb-2"> Email </label>
				<input
					required
					type="email"
					name="email"
					id="email"
					class="shadow border rounded w-full py-2 px-3 leading-tight focus:outline-none text-black"
				/>
			</div>

			<div class="mb-4">
				<label for="password" class="block text-sm font-bold mb-2"> Password </label>
				<input
					required
					type="password"
					name="password"
					id="password"
					class="shadow border rounded w-full py-2 px-3 leading-tight focus:outline-none text-black"
				/>
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
			</div>

			<div class="mb-4">
				<label for="language" class="block text-sm font-bold mb-2"> Default Language </label>
				<input
					required
					type="string"
					name="language"
					id="language"
					class="shadow border rounded w-full py-2 px-3 leading-tight focus:outline-none text-black"
				/>
			</div>
			<div class="flex items-center justify-center mb-4">
				<button
					type="submit"
					class="font-bold py-2 px-4 rounded focus:outline-none bg-blue-700 hover:bg-blue-800 transition"
					>Register</button
				>
			</div>

			<div class="flex items-center justify-center">
				<span class="text-sm"
					>Already have an account? <a href="/login" class="hover:underline">Log in</a></span
				>
			</div>
		</form>
	</div>
</div>
