<script lang="ts">
	export let data;
</script>

<h1 class="text-xl min-[500px]:text-3xl font-bold">Email Sent</h1>
<p>
	{data.message}
	<a class="text-white underline underline-offset-2 hover:text-blue-500" href="/login"
		>Log in here</a
	> after verifying!
</p>
