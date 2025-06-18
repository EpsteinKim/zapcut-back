<template>
	<footer class="p-4 border-t border-gray-200 h-16 flex-shrink-0 z-50 bg-white text-nowrap overflow-hidden">
		<div class="flex items-center justify-between">
			<div v-if="!sidebarStore.isCollapsed" class="flex items-center gap-3">
				<Avatar icon="pi pi-user" size="normal" shape="circle" />
				<div>
					<div class="text-sm font-medium">편집자</div>
					<div class="text-xs">프로젝트: 5개</div>
				</div>
			</div>
			<div v-else class="flex justify-center w-full">
				<Avatar icon="pi pi-user" size="normal" shape="circle" />
			</div>
			<Button v-if="!sidebarStore.isCollapsed" icon="pi pi-cog" class="p-button-text p-button-sm" size="small" />
		</div>
	</footer>
</template>

<script setup lang="ts">
	const sidebarStore = useSidebarStore();
</script>
