<template>
	<div class="relative shadow-lg rounded-xl overflow-hidden">
		<div class="absolute top-3 left-3 z-10">
			<Tag
				severity="warning"
				:value="`${shortsStore.playbackSpeed}x`"
				class="cursor-pointer hover:bg-primary/10"
				@click="isSpeedMenuOpen = !isSpeedMenuOpen"
			/>
			<!-- 재생 속도 선택 메뉴 -->
			<div
				v-if="isSpeedMenuOpen"
				class="absolute top-full left-0 mt-2 bg-white rounded-lg shadow-xl p-3 z-20 min-w-[200px]"
				@mouseleave="isSpeedMenuOpen = false"
			>
				<div class="grid grid-cols-3 gap-2">
					<Tag
						v-for="speed in playbackSpeeds"
						:key="speed"
						severity="warning"
						:value="`${speed}x`"
						class="cursor-pointer transition-all duration-200 hover:bg-primary/10"
						:class="{ 'opacity-50 hover:opacity-75': speed !== shortsStore.playbackSpeed }"
						@click="selectSpeed(speed)"
					/>
				</div>
			</div>
		</div>
		<div class="absolute top-3 right-3 z-10">
			<Button
				:icon="shortsStore.isMuted ? 'pi pi-volume-off' : 'pi pi-volume-up'"
				text
				severity="secondary"
				class="text-white bg-black/50 hover:bg-black/60"
				@click="toggleMute"
			/>
		</div>
		<div style="aspect-ratio: 9/16" class="relative">
			<video
				v-if="shortsStore.videoUrl"
				ref="videoRef"
				class="object-cover bg-black w-full h-full"
				:src="shortsStore.videoUrl"
				:playbackRate="shortsStore.playbackSpeed"
				:muted="shortsStore.isMuted"
				preload="metadata"
				@timeupdate="handleTimeUpdate"
				@loadedmetadata="handleVideoLoaded"
				@ended="handleVideoEnded"
			>
				<source :src="shortsStore.videoUrl" type="video/mp4" />
				브라우저가 비디오를 지원하지 않습니다.
			</video>
			<template v-else-if="shortsStore.composedVideoUrl">
				<video
					ref="videoRef"
					class="object-cover bg-black w-full h-full"
					:src="shortsStore.composedVideoUrl"
					:playbackRate="shortsStore.playbackSpeed"
					playsinline
					:muted="shortsStore.isMuted"
					preload="metadata"
					@timeupdate="handleTimeUpdate"
					@loadedmetadata="handleVideoLoaded"
				>
					<source :src="shortsStore.composedVideoUrl" type="video/webm" />
					브라우저가 비디오를 지원하지 않습니다.
				</video>

				<div v-if="shortsStore.currentScene?.voiceUrl" class="absolute inset-0 flex flex-col items-center justify-center">
					<div
						class="text-white text-center px-4 py-2 max-w-[80%] [filter:drop-shadow(0_0_2px_#000)_drop-shadow(0_0_2px_#000)_drop-shadow(0_0_2px_#000)_drop-shadow(0_0_2px_#000)]"
					>
						<template v-for="(caption, index) in shortsStore.currentCaptions" :key="index">
							<div class="text-2xl font-bold mb-2">{{ caption.text }}</div>
						</template>
					</div>
				</div>
			</template>
			<div v-else class="w-full h-full bg-black flex flex-col items-center justify-center">
				<div v-if="shortsStore.currentScene?.imageUrl" class="absolute inset-0 bg-cover bg-center flex items-center justify-center">
					<img :src="shortsStore.currentScene.imageUrl" class="max-h-full max-w-full object-contain" alt="Scene image" />
				</div>
				<div v-if="shortsStore.currentScene?.voiceUrl" class="absolute inset-0 flex flex-col items-center justify-center">
					<div
						class="text-white text-center px-4 py-2 max-w-[80%] [filter:drop-shadow(0_0_2px_#000)_drop-shadow(0_0_2px_#000)_drop-shadow(0_0_2px_#000)_drop-shadow(0_0_2px_#000)]"
					>
						<template v-for="(caption, index) in shortsStore.currentCaptions" :key="index">
							<div class="text-2xl font-bold mb-2">{{ caption.text }}</div>
						</template>
					</div>
				</div>
				<div v-else class="text-white text-center">재생할 음성이 없습니다.</div>
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

	const handleTimeUpdate = () => {
		if (!videoRef.value) return;
		shortsStore.setCurrentTime(videoRef.value.currentTime);
	};

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
			if (shortsStore.composedAudio) {
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
