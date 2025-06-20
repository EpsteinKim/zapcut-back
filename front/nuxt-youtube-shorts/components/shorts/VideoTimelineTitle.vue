<template>
	<div class="h-[40px] flex items-center px-2 text-xs font-medium justify-around">
		<i :class="iconClass + ' flex-1'"></i>
		<Typography class="flex-2 text-center">{{ title }}</Typography>
	</div>
</template>

<script setup lang="ts">
	interface Props {
		iconClass: string;
		title: string;
	}

	defineProps<Props>();
</script>
