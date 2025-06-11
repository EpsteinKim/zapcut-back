<template>
    <div>
        <!-- 헤더 -->
        <header class="flex justify-between items-center bg-surface-0">
            <div class="flex items-center space-x-4">
                <Button icon="pi pi-arrow-left" text @click="handleBack" />
                <h1 class="text-xl font-semibold">비디오 편집</h1>
            </div>
            <div class="flex items-center space-x-4">
                <Button label="미리보기" icon="pi pi-eye" outlined />
                <Button label="저장" icon="pi pi-save" severity="primary" />
            </div>
        </header>

        <div class="flex overflow-hidden">
            <!-- 좌측: 비디오 프리뷰 -->
            <div class="bg-surface-0 p-6 flex flex-col">
                <div class="w-[425px]">
                    <!-- 비디오 프리뷰 -->
                    <VideoPreview
                        ref="videoPreviewRef"
                        :video-url="shortsStore.videoUrl"
                        :speed="shortsStore.playbackSpeed"
                        :is-muted="shortsStore.isMuted"
                        :current-time="shortsStore.currentTime"
                        :duration="shortsStore.duration"
                        @update:current-time="shortsStore.setTime"
                        @update:duration="shortsStore.setDuration"
                        @toggle-mute="shortsStore.toggleMute"
                    />
                    <VideoControls class="mt-6" :is-playing="shortsStore.isPlaying" @toggle-play="handleTogglePlay" @seek="shortsStore.seekRelative" />

                    <Divider />

                    <div class="text-center text-sm text-slate-500">
                        <i class="pi pi-info-circle mr-2"></i>
                        {{ shortsStore.script?.title }}
                    </div>
                </div>
            </div>

            <!-- 우측: 타임라인 & 스크립트 -->
            <div class="flex flex-col overflow-hidden">
                <div class="p-4">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-xl font-semibold">타임라인</h3>
                        <Tag severity="info" :value="`${formatTime(shortsStore.currentTime)} / ${formatTime(shortsStore.totalDuration)}`" />
                    </div>
                    <div class="h-[200px] overflow-x-auto overflow-y-hidden">
                        <div class="relative h-full" :style="{ width: `${shortsStore.totalDuration * 100}px` }">
                            <!-- 시간 눈금 -->
                            <div class="absolute top-0 left-0 right-0 h-6 flex">
                                <div
                                    v-for="i in Math.ceil(shortsStore.totalDuration)"
                                    :key="i"
                                    class="flex-none w-[100px] border-r border-slate-200 text-xs text-slate-500 pt-1"
                                >
                                    {{ formatTime(i - 1) }}
                                </div>
                            </div>

                            <!-- 현재 시간 커서 -->
                            <div
                                class="absolute top-0 bottom-0 w-0.5 bg-primary z-10"
                                :style="{ left: `${(shortsStore.currentTime / shortsStore.totalDuration) * 100}%` }"
                            ></div>

                            <!-- 트랙 -->
                            <div class="absolute top-6 left-0 right-0 bottom-0">
                                <!-- 배경음악 트랙 -->
                                <div class="h-8 mb-2 bg-emerald-100/50 relative">
                                    <div class="absolute inset-y-0 left-2 flex items-center">
                                        <i class="pi pi-volume-up mr-2"></i>
                                        <span class="text-xs">배경음악</span>
                                    </div>
                                </div>

                                <!-- 영상 트랙 -->
                                <div class="h-8 mb-2 bg-blue-100/50 relative">
                                    <div class="absolute inset-y-0 left-2 flex items-center">
                                        <i class="pi pi-video mr-2"></i>
                                        <span class="text-xs">영상</span>
                                    </div>
                                </div>

                                <!-- 음성 트랙 -->
                                <div class="h-8 mb-2 bg-orange-100/50 relative">
                                    <div class="absolute inset-y-0 left-2 flex items-center">
                                        <i class="pi pi-microphone mr-2"></i>
                                        <span class="text-xs">음성</span>
                                    </div>
                                    <!-- 음성 세그먼트 -->
                                    <div
                                        v-for="(scene, index) in shortsStore.script?.scene"
                                        :key="index"
                                        class="absolute h-full bg-orange-200 rounded"
                                        :style="{
                                            left: `${getSceneStartTime(index) * 100}px`,
                                            width: `${scene.duration * 100}px`
                                        }"
                                    ></div>
                                </div>

                                <!-- 자막 트랙 -->
                                <div class="h-8 bg-purple-100/50 relative">
                                    <div class="absolute inset-y-0 left-2 flex items-center">
                                        <i class="pi pi-list mr-2"></i>
                                        <span class="text-xs">자막</span>
                                    </div>
                                    <!-- 자막 세그먼트 -->
                                    <div v-for="(scene, sceneIndex) in shortsStore.script?.scene" :key="sceneIndex">
                                        <div
                                            v-for="(caption, captionIndex) in scene.captions"
                                            :key="captionIndex"
                                            class="absolute h-full bg-purple-200 rounded"
                                            :style="{
                                                left: `${(getSceneStartTime(sceneIndex) + caption.start_time) * 100}px`,
                                                width: `${(caption.end_time - caption.start_time) * 100}px`
                                            }"
                                        >
                                            <span class="text-xs px-1 truncate">{{ caption.text }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 스크립트 & 음성 정보 -->
                <div class="flex-1 p-4">
                    <div class="mb-4">
                        <h3 class="text-lg font-semibold mb-2">생성된 스크립트 & 음성</h3>
                        <div class="bg-surface-0 rounded-lg">
                            <div class="mb-4">
                                <Tag icon="pi pi-clock" severity="info" :value="`${shortsStore.totalDuration}초`" class="mr-2" />
                                <Tag icon="pi pi-volume-up" severity="success" value="AI 음성 생성됨" />
                            </div>
                            <div class="space-y-4 overflow-y-auto h-[500px]">
                                <div v-for="(scene, index) in shortsStore.script?.scene" :key="index" class="p-4 bg-surface-50 rounded-lg">
                                    <div class="flex justify-between items-center mb-2">
                                        <span class="font-medium">씬 {{ index + 1 }}</span>
                                        <Tag :value="`${scene.duration}초`" />
                                    </div>
                                    <div class="space-y-2">
                                        <div v-for="(caption, cIndex) in scene.captions" :key="cIndex" class="flex items-center justify-between text-sm">
                                            <span>{{ caption.text }}</span>
                                            <span class="text-slate-500">{{ formatTime(caption.start_time) }} - {{ formatTime(caption.end_time) }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    import { ref } from 'vue'
    import { useShortsStore } from '~/stores/shorts'
    import type { Scene } from '~/types/api'
    import { VideoPreview, VideoControls } from '#components'

    const shortsStore = useShortsStore()
    const videoPreviewRef = ref<InstanceType<typeof VideoPreview> | null>(null)

    const handleBack = () => {
        window.history.back()
    }

    const handleTogglePlay = () => {
        if (!videoPreviewRef.value) return
        shortsStore.togglePlay()
        if (shortsStore.isPlaying) {
            videoPreviewRef.value.play()
        } else {
            videoPreviewRef.value.pause()
        }
    }

    // 특정 씬의 시작 시간 계산
    const getSceneStartTime = (sceneIndex: number) => {
        if (!shortsStore.script?.scene) return 0
        return shortsStore.script.scene.slice(0, sceneIndex).reduce((acc: number, scene: Scene) => acc + scene.duration, 0)
    }

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }
</script>
