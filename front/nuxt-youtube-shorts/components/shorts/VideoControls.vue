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
		if (timer) {
			clearInterval(timer);
			timer = null;
		}
		const toTime = shortsStore.currentTime + offset;
		const clampedTime = Math.max(0, Math.min(toTime, shortsStore.totalDuration));

		shortsStore.seekVideo(clampedTime);
		startTimer();
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
			startTimer();

			if (shortsStore.videoElement) {
				shortsStore.videoElement.currentTime = shortsStore.currentTime;
				shortsStore.videoElement.play();
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
