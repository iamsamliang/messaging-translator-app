<script lang="ts">
	export let data;
</script>

<div class="min-h-screen bg-black flex flex-col">
	<!-- Header -->
	<header class="bg-black text-white sticky top-0 z-50">
		<div class="max-w-[1440px] mx-auto px-[1rem] md:px-12 py-5">
			<nav class="px-6 py-4 flex items-center justify-between">
				<!-- Logo -->
				<div>
					<a href="/">
						<img src="/images/logo-white.svg" alt="Logo" class="h-12" />
					</a>
				</div>
				<!-- w-auto gap-x-[40px] hidden lg:flex justify-between items-center font-normal text-base text-blue-100 -->
				<div class="w-auto gap-x-[40px] flex items-center justify-between">
					{#if data.user}
						<a
							href="/chat"
							class="font-semibold border-none cursor-pointer text-white-700 hover:text-blue-100 transition"
						>
							Chat Now, {data.user.first_name.charAt(0).toUpperCase() +
								data.user.first_name.slice(1)}
						</a>
						<a
							href="/logout"
							class="bg-gray-800 px-6 py-2 rounded-full hover:bg-gray-700 transition"
						>
							Log out
						</a>
					{:else}
						<!-- text-base font-semibold border-none hover:underline cursor-pointer text-blue-100 hover:text-blue-100 text-white-700 hover:text-white-700 -->
						<a
							href="/signup"
							class="font-semibold border-none cursor-pointer text-white-700 hover:text-blue-100 transition"
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
			</nav>
		</div>
	</header>

	<!-- Landing Page -->
	<div class="mb-auto">
		<div class="relative bg-black h-full flex flex-col justify-between items-center">
			<section class="w-full">
				<section class="bg-black relative w-full flex flex-col items-center justify-center">
					<div class="max-w-[1440px] mx-auto px-[1rem] md:px-12 relative">
						<div class="flex lg:flex-row gap-x-4 items-start lg:items-center gap-y-16 flex-col">
							<div class="flex flex-1 flex-col pt-4 md:pt-8 sm:pt-0">
								<div class="uppercase mb-3 lg:mb-4 text-base text-gray-200">
									<h1 class="uppercase mb-3 lg:mb-4 text-base text-gray-200">
										Breaking the Communication Barrier
									</h1>
								</div>
								<div
									class="font-bold text-white text-4xl md:text-[64px] lg:text-[80px] md:leading-[120%] mb-6 lg:mb-8"
								>
									<h2 class="text-white text-4xl md:leading-[120%] mb-6 md:text-[74px] font-medium">
										Chat With Anyone, Using Any Language of Your Choice
									</h2>
								</div>
								<div class="text-lg text-gray-200 mb-20">
									<p>
										Pick your language of choice, and we will translate any messages sent your way
										to that language.
									</p>
								</div>
								<div>
									<a
										href="/login"
										class="text-lg bg-white font-semibold px-6 py-4 rounded-full hover:bg-blue-200 transition"
										>Start Chatting Now</a
									>
								</div>
							</div>
						</div>
					</div>
				</section>
			</section>
		</div>
	</div>

	<!-- Footer -->
	<footer>
		<div class="flex justify-center items-center mb-5">
			<span class="text-white">&copy; SpeakeAIsy</span>
		</div>
	</footer>
</div>
