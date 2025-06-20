<template>
	<div class="flex flex-col items-center space-y-3 md:space-y-4">
		<div class="flex justify-center space-x-3 md:space-x-4">
			<Button icon="pi pi-backward" rounded text size="small" class="hover:bg-primary/10 w-10 h-10 md:w-12 md:h-12" @click="seekRelative(-5)" />
			<Button
				:icon="shortsStore.isPlaying ? 'pi pi-pause' : 'pi pi-play'"
				rounded
				severity="primary"
				:size="isMobile ? 'normal' : 'large'"
				class="w-12 h-12 md:w-14 md:h-14"
				@click="togglePlay"
			/>
			<Button icon="pi pi-forward" rounded text size="small" class="hover:bg-primary/10 w-10 h-10 md:w-12 md:h-12" @click="seekRelative(5)" />
		</div>
	</div>
</template>

<script setup lang="ts">
	const shortsStore = useShortsStore();
	const isMobile = ref(false);
	let timer: ReturnType<typeof setInterval> | null = null;

	onMounted(() => {
		isMobile.value = window.innerWidth < 768;
		window.addEventListener('resize', () => {
			isMobile.value = window.innerWidth < 768;
		});
	});

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
