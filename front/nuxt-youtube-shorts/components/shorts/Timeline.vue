<template>
    <div class="flex flex-col h-full">
        <!-- 시간 눈금자 -->
        <div class="h-8 border-b relative">
            <div class="absolute inset-0 flex">
                <div v-for="i in Math.ceil(totalDuration)" :key="i" class="flex-1 border-r last:border-r-0 relative">
                    <span class="absolute -bottom-6 left-0 text-xs text-slate-500">
                        {{ formatTime(i - 1) }}
                    </span>
                </div>
            </div>
            <!-- 현재 시간 커서 -->
            <div
                class="absolute top-0 bottom-0 w-0.5 bg-primary z-10"
                :style="{
                    left: `${(currentTime / totalDuration) * 100}%`
                }"
            ></div>
        </div>

        <!-- 트랙 목록 -->
        <div class="flex-1 overflow-y-auto space-y-2 mt-8">
            <div v-for="track in tracks" :key="track.id" class="relative h-16 bg-slate-100 rounded-lg">
                <!-- 트랙 레이블 -->
                <div class="absolute -left-20 top-1/2 -translate-y-1/2 w-16 text-sm text-slate-600">
                    {{ track.label }}
                </div>

                <!-- 세그먼트 -->
                <div
                    v-for="segment in track.segments"
                    :key="segment.id"
                    class="absolute top-0 bottom-0 rounded"
                    :class="segment.type === 'voice' ? 'bg-blue-200' : 'bg-green-200'"
                    :style="{
                        left: `${(segment.start / totalDuration) * 100}%`,
                        width: `${((segment.end - segment.start) / totalDuration) * 100}%`
                    }"
                >
                    <div class="p-2 text-xs truncate">
                        {{ segment.content }}
                    </div>

                    <!-- 삭제 버튼 -->
                    <Button
                        icon="pi pi-times"
                        text
                        severity="danger"
                        size="small"
                        class="absolute -top-2 -right-2"
                        @click="$emit('remove-segment', track.id, segment.id)"
                    />
                </div>

                <!-- 세그먼트 추가 버튼 -->
                <Button icon="pi pi-plus" text class="absolute -right-12 top-1/2 -translate-y-1/2" @click="$emit('add-segment', track.id)" />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    interface Segment {
        id: string
        type: 'voice' | 'background' | 'text'
        content: string
        start: number
        end: number
    }

    interface Track {
        id: string
        label: string
        segments: Segment[]
    }

    const props = defineProps<{
        currentTime: number
        totalDuration: number
        tracks: Track[]
    }>()

    defineEmits<{
        'add-segment': [trackId: string]
        'remove-segment': [trackId: string, segmentId: string]
        'update-segment': [trackId: string, segmentId: string, updates: Partial<Track>]
    }>()

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }
</script>
