<template>
    <ScriptGenerator v-if="!shortsStore.script" />
    <VideoEditor v-else />
</template>

<script setup lang="ts">
    const shortsStore = useShortsStore()
</script>
