<template>
	<div class="relative shadow-lg rounded-xl overflow-hidden mx-auto max-w-xs md:max-w-sm lg:max-w-md">
		<div class="absolute top-2 md:top-3 left-2 md:left-3 z-10">
			<Tag
				severity="warning"
				:value="`${shortsStore.playbackSpeed}x`"
				class="cursor-pointer hover:bg-primary/10 text-xs md:text-sm"
				@click="isSpeedMenuOpen = !isSpeedMenuOpen"
			/>
			<!-- 재생 속도 선택 메뉴 -->
			<div
				v-if="isSpeedMenuOpen"
				class="absolute top-full left-0 mt-2 bg-white rounded-lg shadow-xl p-2 md:p-3 z-20 min-w-[160px] md:min-w-[200px]"
				@mouseleave="isSpeedMenuOpen = false"
				@touchend="isSpeedMenuOpen = false"
			>
				<div class="grid grid-cols-3 gap-1 md:gap-2">
					<Tag
						v-for="speed in playbackSpeeds"
						:key="speed"
						severity="warning"
						:value="`${speed}x`"
						class="cursor-pointer transition-all duration-200 hover:bg-primary/10 text-xs md:text-sm"
						:class="{ 'opacity-50 hover:opacity-75': speed !== shortsStore.playbackSpeed }"
						@click="selectSpeed(speed)"
						@touchend="selectSpeed(speed)"
					/>
				</div>
			</div>
		</div>
		<div class="absolute top-2 md:top-3 right-2 md:right-3 z-10">
			<Button
				:icon="shortsStore.isMuted ? 'pi pi-volume-off' : 'pi pi-volume-up'"
				text
				severity="secondary"
				size="small"
				class="text-white bg-black/50 hover:bg-black/60"
				@click="toggleMute"
			/>
		</div>
		<div class="relative w-full" style="aspect-ratio: 9/16; container-type: inline-size">
			<video
				v-if="shortsStore.videoUrl"
				ref="videoRef"
				class="absolute inset-0 w-full h-full object-cover bg-black"
				:src="shortsStore.videoUrl"
				:playbackRate="shortsStore.playbackSpeed"
				:muted="shortsStore.isMuted"
				preload="metadata"
				playsinline
				@loadedmetadata="handleVideoLoaded"
				@ended="handleVideoEnded"
			>
				<source :src="shortsStore.videoUrl" type="video/mp4" />
				브라우저가 비디오를 지원하지 않습니다.
			</video>
			<template v-else-if="shortsStore.composedVideoUrl">
				<video
					ref="videoRef"
					class="absolute inset-0 w-full h-full object-cover bg-black"
					:src="shortsStore.composedVideoUrl"
					:playbackRate="shortsStore.playbackSpeed"
					playsinline
					:muted="shortsStore.isMuted"
					preload="metadata"
					@loadedmetadata="handleVideoLoaded"
					@ended="handleVideoEnded"
				>
					<source :src="shortsStore.composedVideoUrl" type="video/webm" />
					브라우저가 비디오를 지원하지 않습니다.
				</video>

				<CaptionOverlay v-if="shortsStore.currentScene?.voiceUrl" :captions="shortsStore.currentCaptions" />
			</template>
			<div v-else class="absolute inset-0 bg-black flex flex-col items-center justify-center">
				<div v-if="shortsStore.currentScene?.imageUrl" class="absolute inset-0 flex items-center justify-center">
					<img :src="shortsStore.currentScene.imageUrl" class="max-h-full max-w-full object-contain" alt="Scene image" />
				</div>
				<CaptionOverlay v-if="shortsStore.currentScene?.voiceUrl" :captions="shortsStore.currentCaptions" />
				<div v-else class="text-white text-center text-sm md:text-base">재생할 음성이 없습니다.</div>
			</div>
		</div>
		<!-- 재생 진행바 -->
		<div class="absolute bottom-0 left-0 right-0 h-1 bg-black/20">
			<div
				class="h-full bg-primary"
				:style="{
					width: `${(shortsStore.currentTime / shortsStore.totalDuration) * 100}%`
				}"
			></div>
		</div>
	</div>
</template>

<script setup lang="ts">
	const shortsStore = useShortsStore();
	const videoRef = ref<HTMLVideoElement | null>(null);
	const isSpeedMenuOpen = ref(false);
	const playbackSpeeds = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];

	const handleVideoLoaded = () => {
		if (!videoRef.value) return;
		shortsStore.setDuration(videoRef.value.duration);
	};

	const handleVideoEnded = () => {
		console.log(videoRef.value?.currentTime);
		shortsStore.setCurrentTime(0);
		shortsStore.setIsPlaying(false);
	};

	const selectSpeed = (speed: number) => {
		shortsStore.setPlaybackSpeed(speed);
		isSpeedMenuOpen.value = false;
	};

	const toggleMute = () => {
		shortsStore.setIsMuted(!shortsStore.isMuted);
	};

	watch(
		() => shortsStore.playbackSpeed,
		(newSpeed) => {
			if (shortsStore.composedAudio && shortsStore.isPlaying) {
				shortsStore.composedAudio.play(shortsStore.currentTime, newSpeed);
			}
		}
	);
	watch(
		() => videoRef.value,
		(newVideoRef) => {
			shortsStore.setVideoElement(newVideoRef as HTMLVideoElement);
		}
	);
	watch(
		() => shortsStore.isMuted,
		(newMuted) => {
			if (shortsStore.composedAudio) {
				shortsStore.composedAudio.setVolume(newMuted ? 0 : 1);
			}
		}
	);
</script>
