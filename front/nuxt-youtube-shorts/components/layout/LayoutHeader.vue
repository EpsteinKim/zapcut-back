<template>
    <header
        class="flex items-center justify-between p-4 h-16 ml-0 border-b border-gray-200 bg-white text-nowrap overflow-hidden"
    >
        <div class="flex items-center gap-3 text-nowrap justify-center">
            <Avatar
                v-if="!sidebarStore.isCollapsed"
                icon="pi pi-video"
                class="mr-2 bg-purple-300!"
                :class="sidebarStore.isCollapsed ? 'w-8 h-8' : 'w-16 h-16'"
                shape="circle"
                size="medium"
            />
            <div v-if="!sidebarStore.isCollapsed">
                <h2 class="font-semibold text-lg">비디오 편집기</h2>
                <p class="text-xs">YouTube Shorts</p>
            </div>
        </div>
        <Button
            :icon="
                sidebarStore.isCollapsed
                    ? 'pi pi-angle-right'
                    : 'pi pi-angle-left'
            "
            :class="[sidebarStore.isCollapsed ? 'mx-auto' : 'ml-0']"
            variant="text"
            @click="sidebarStore.toggleSidebar()"
        />
    </header>
</template>

<script setup lang="ts">
    const sidebarStore = useSidebarStore()
</script>
