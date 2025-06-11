<template>
    <div class="relative shadow-lg rounded-xl overflow-hidden">
        <div class="absolute top-3 left-3 z-10">
            <Tag severity="warning" :value="`${speed}x`" />
        </div>
        <div class="absolute top-3 right-3 z-10">
            <Button
                :icon="isMuted ? 'pi pi-volume-off' : 'pi pi-volume-up'"
                text
                severity="secondary"
                class="text-white bg-black/50 hover:bg-black/60"
                @click="$emit('toggle-mute')"
            />
        </div>
        <div style="aspect-ratio: 9/16">
            <video
                ref="videoRef"
                class="object-cover bg-black w-full h-full"
                :src="videoUrl"
                @timeupdate="handleTimeUpdate"
                @loadedmetadata="handleVideoLoaded"
                :playbackRate="speed"
                :muted="isMuted"
            >
                <source :src="videoUrl" type="video/mp4" />
                브라우저가 비디오를 지원하지 않습니다.
            </video>
        </div>
        <!-- 재생 진행바 -->
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-black/20">
            <div
                class="h-full bg-primary"
                :style="{
                    width: `${(currentTime / duration) * 100}%`
                }"
            ></div>
        </div>
    </div>
</template>

<script setup lang="ts">
    import { ref, watch } from 'vue'

    const props = defineProps<{
        videoUrl: string
        speed: number
        isMuted: boolean
        currentTime: number
        duration: number
    }>()

    const emit = defineEmits<{
        'update:currentTime': [time: number]
        'update:duration': [duration: number]
        'toggle-mute': []
    }>()

    const videoRef = ref<HTMLVideoElement | null>(null)

    const handleTimeUpdate = () => {
        if (!videoRef.value) return
        emit('update:currentTime', videoRef.value.currentTime)
    }

    const handleVideoLoaded = () => {
        if (!videoRef.value) return
        emit('update:duration', videoRef.value.duration)
    }

    // 재생 속도 변경 감시
    watch(
        () => props.speed,
        (newSpeed) => {
            if (!videoRef.value) return
            videoRef.value.playbackRate = newSpeed
        }
    )

    // 비디오 요소 메서드를 외부로 노출
    defineExpose({
        play: () => videoRef.value?.play(),
        pause: () => videoRef.value?.pause(),
        seek: (time: number) => {
            if (!videoRef.value) return
            videoRef.value.currentTime = time
        }
    })
</script>
