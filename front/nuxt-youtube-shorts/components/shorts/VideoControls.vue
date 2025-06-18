<template>
	<div class="flex flex-col items-center space-y-4">
		<!-- 재생 컨트롤 -->
		<div class="flex justify-center space-x-4">
			<Button icon="pi pi-backward" rounded text class="hover:bg-primary/10" @click="seekRelative(-5)" />
			<Button :icon="shortsStore.isPlaying ? 'pi pi-pause' : 'pi pi-play'" rounded severity="primary" size="large" @click="togglePlay" />
			<Button icon="pi pi-forward" rounded text class="hover:bg-primary/10" @click="seekRelative(5)" />
		</div>
	</div>
</template>

<script setup lang="ts">
	const shortsStore = useShortsStore();
	let timer: ReturnType<typeof setInterval> | null = null;

	const hasNoVideo = computed(() => !shortsStore.videoUrl && !shortsStore.composedVideoUrl);

	// 비디오가 없을 때 타이머로 시간 업데이트
	const startTimer = () => {
		if (timer) return;
		timer = setInterval(() => {
			if (!shortsStore.isPlaying) return;
			const newTime = shortsStore.currentTime + 0.025 * shortsStore.playbackSpeed;
			if (newTime >= shortsStore.totalDuration) {
				shortsStore.setCurrentTime(0);
				shortsStore.setIsPlaying(false);
				if (timer) clearInterval(timer);
				return;
			}
			shortsStore.setCurrentTime(newTime);
		}, 25);
	};

	// seek 기능 구현
	const seekRelative = (offset: number) => {
		const toTime = shortsStore.currentTime + offset;
		const clampedTime = Math.max(0, Math.min(toTime, shortsStore.totalDuration));

		if ((shortsStore.videoUrl || shortsStore.composedVideoUrl) && shortsStore.videoElement) {
			shortsStore.videoElement.currentTime = clampedTime;
		}

		shortsStore.setCurrentTime(clampedTime);

		if (timer) {
			clearInterval(timer);
			timer = null;
		}

		if (hasNoVideo.value) {
			startTimer();
		}

		if (!shortsStore.videoUrl) {
			shortsStore.composedAudio?.play(clampedTime, shortsStore.playbackSpeed);
		}
	};

	const togglePlay = () => {
		const isPlaying = shortsStore.isPlaying;
		if (isPlaying) {
			if (timer) {
				clearInterval(timer);
				timer = null;
			}
			if (shortsStore.videoElement) {
				shortsStore.videoElement.pause();
			}
			shortsStore.composedAudio?.stop();
			shortsStore.setIsPlaying(false);
		} else {
			if (hasNoVideo.value) {
				startTimer();
			} else {
				shortsStore.videoElement?.play();
			}

			if (!shortsStore.videoUrl) {
				shortsStore.composedAudio?.play(shortsStore.currentTime, shortsStore.playbackSpeed);
			}
			shortsStore.setIsPlaying(true);
		}
	};

	onUnmounted(() => {
		if (timer) {
			clearInterval(timer);
			timer = null;
		}
		shortsStore.composedAudio?.cleanup();
	});
</script>
