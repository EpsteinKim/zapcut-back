<template>
    <div class="flex bg-gray-50">
        <div
            :class="['flex flex-col h-screen fixed bg-white border-r border-gray-200 transition-all duration-300', sidebarStore.isCollapsed ? 'w-20' : 'w-80']"
        >
            <LayoutHeader />
            <LayoutMenu />
            <LayoutFooter />
        </div>

        <main
            :class="[
                'absolute transition-all duration-300 overflow-y-auto h-screen p-6',
                sidebarStore.isCollapsed ? 'left-20 w-[calc(100%-5rem)]' : 'left-80 w-[calc(100%-20rem)]'
            ]"
        >
            <div class="max-w-screen-2xl mx-auto">
                <slot />
            </div>
        </main>
    </div>
</template>

<script setup lang="ts">
    import { useSidebarStore } from '~/stores/sidebar'
    import { onMounted, onUnmounted } from 'vue'

    const sidebarStore = useSidebarStore()

    const handleResize = (e: MediaQueryListEvent | MediaQueryList) => {
        if (e.matches) {
            sidebarStore.collapse()
        } else {
            sidebarStore.sperad()
        }
    }

    onMounted(() => {
        const mediaQuery = window.matchMedia('(max-width: 1072px)')
        mediaQuery.addEventListener('change', handleResize)
        handleResize(mediaQuery)
    })

    onUnmounted(() => {
        const mediaQuery = window.matchMedia('(max-width: 1072px)')
        mediaQuery.removeEventListener('change', handleResize)
    })
</script>
