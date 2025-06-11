<template>
    <div class="flex flex-col items-center">
        <h3 class="text-lg font-medium mb-4">재생 속도</h3>
        <div class="flex items-center space-x-2">
            <Button
                v-for="speed in speeds"
                :key="speed"
                :label="`${speed}x`"
                :severity="modelValue === speed ? 'primary' : 'secondary'"
                :outlined="modelValue !== speed"
                @click="$emit('update:modelValue', speed)"
            />
        </div>
    </div>
</template>

<script setup lang="ts">
    const speeds = [0.5, 1, 1.5, 2]

    defineProps<{
        modelValue: number
    }>()

    defineEmits<{
        'update:modelValue': [speed: number]
    }>()
</script>
