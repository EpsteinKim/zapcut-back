<template>
    <section class="flex-1 overflow-hidden text-nowrap">
        <div class="p-3 h-full">
            <PanelMenu
                :model="panelMenuItems"
                class="w-full border-none"
                :class="{ 'collapsed-menu': sidebarStore.isCollapsed }"
                :style="{
                    backgroundColor: 'transparent',
                    border: 'none'
                }"
            />
        </div>
    </section>
</template>

<script setup lang="ts">
    const sidebarStore = useSidebarStore()

    const panelMenuItems = computed(() => [
        {
            key: 'editing',
            label: sidebarStore.isCollapsed ? undefined : '편집 도구',
            icon: 'pi pi-video',
            class: sidebarStore.isCollapsed ? 'justify-center' : '',
            items: sidebarStore.isCollapsed
                ? undefined
                : [
                      {
                          label: '스크립트 생성',
                          icon: 'pi pi-file-edit'
                      },
                      {
                          label: '비디오 편집',
                          icon: 'pi pi-video'
                      }
                  ]
        }
    ])
</script>
