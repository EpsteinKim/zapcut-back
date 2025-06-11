<template>
    <div class="flex justify-center space-x-4">
        <Button icon="pi pi-backward" rounded text class="hover:bg-primary/10" @click="$emit('seek', -5)" />
        <Button :icon="isPlaying ? 'pi pi-pause' : 'pi pi-play'" rounded severity="primary" size="large" @click="$emit('toggle-play')" />
        <Button icon="pi pi-forward" rounded text class="hover:bg-primary/10" @click="$emit('seek', 5)" />
    </div>
</template>

<script setup lang="ts">
    defineProps<{
        isPlaying: boolean
    }>()

    defineEmits<{
        'toggle-play': []
        seek: [seconds: number]
    }>()
</script>
