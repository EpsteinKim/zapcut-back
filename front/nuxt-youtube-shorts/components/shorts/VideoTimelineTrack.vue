<template>
	<div class="h-8 mb-2 relative flex">
		<!-- 라벨 영역 (sticky) -->
		<div class="sticky left-0 w-[100px] bg-inherit flex items-center px-2 z-10">
			<i :class="`pi pi-${icon} mr-2`" />
			<span class="text-xs truncate max-w-[70px]">{{ label }}</span>
		</div>
		<!-- 컨텐츠 영역 (scrollable) -->
		<div class="relative flex-1 overflow-visible" :class="bgColorClass">
			<slot />
		</div>
	</div>
</template>

<script setup lang="ts">
	interface Props {
		icon: string;
		label: string;
		type: 'bgm' | 'video' | 'voice' | 'caption';
	}

	const props = defineProps<Props>();

	const bgColorClass = computed(() => {
		const colors = {
			bgm: 'bg-emerald-100/50',
			video: 'bg-blue-100/50',
			voice: 'bg-orange-100/50',
			caption: 'bg-purple-100/50'
		};
		return colors[props.type];
	});
</script>
