<script>
	import { page } from '$app/stores';
</script>

<h1 class="text-xl min-[500px]:text-3xl font-bold">Error</h1>
<p>
	{$page.error?.message}
	<a class="text-white underline underline-offset-2 hover:text-blue-500" href="/"
		>Return Back Here</a
	>
</p>
