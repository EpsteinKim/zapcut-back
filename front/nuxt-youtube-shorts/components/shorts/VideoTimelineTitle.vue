<template>
	<div class="h-8 md:h-10 flex items-center px-2 text-xs sm:text-sm font-medium border-b border-gray-200 bg-white hover:bg-gray-50 transition-colors">
		<i :class="iconClass + ' text-gray-600 mr-1 sm:mr-2 text-xs sm:text-sm'"></i>
		<span class="text-gray-700 font-medium truncate">{{ title }}</span>
	</div>
</template>

<script setup lang="ts">
	interface Props {
		iconClass: string;
		title: string;
	}

	defineProps<Props>();
</script>
