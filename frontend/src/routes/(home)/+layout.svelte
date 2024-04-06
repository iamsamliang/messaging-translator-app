<div class="min-h-screen bg-black flex flex-col">
	<!-- Nav Bar w/ Logo -->
	<header class="text-white">
		<div class="px-4 md:px-8 lg:px-20 py-5">
			<nav class="px-6 py-4 flex items-center justify-center md:justify-normal">
				<div>
					<a href="/">
						<img src="/images/logo-white.svg" alt="Logo" class="h-12" />
					</a>
				</div>
			</nav>
		</div>
	</header>
	<slot />
	<!-- Footer -->
	<footer class="mt-auto">
		<div class="flex justify-center items-center mb-5">
			<span class="text-white">&copy; Sam Liang</span>
		</div>
	</footer>
</div>
