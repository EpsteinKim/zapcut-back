<template>
	<div class="flex flex-col">
		<div class="flex items-center justify-between mb-4">
			<h3 class="text-lg pl-2 font-semibold">타임라인</h3>
			<Tag severity="help" icon="pi pi-info-circle" value="Ctrl 또는 Command(⌘) 키를 누른 상태에서 타임라인을 클릭하세요" />
			<Tag severity="info" :value="`${formatTime(shortsStore.currentTime)} / ${formatTime(shortsStore.totalDuration)}`" />
		</div>

		<div ref="timelineRef" class="flex">
			<div class="flex-none w-[100px] bg-white">
				<div class="h-6"></div>
				<div class="h-6"></div>
				<div class="flex flex-col">
					<VideoTimelineTitle icon-class="pi pi-volume-up" title="배경음악" />
					<VideoTimelineTitle icon-class="pi pi-video" title="영상" />
					<VideoTimelineTitle icon-class="pi pi-microphone" title="음성" />
					<VideoTimelineTitle icon-class="pi pi-list" title="자막" />
				</div>
				<div class="h-4" aria-label="트랙 스크롤 라벨 영역"></div>
			</div>

			<div class="flex-1 overflow-x-auto cursor-pointer" @wheel="handleWheel" @click="(e) => (e.ctrlKey || e.metaKey) && handleTimelineClick(e)">
				<div class="relative flex flex-col" :style="{ width: `${shortsStore.totalDuration * 200}px` }">
					<div class="h-6 flex border-b border-slate-200 bg-white sticky top-0">
						<div
							v-for="i in Math.ceil(shortsStore.totalDuration * 2)"
							:key="i"
							class="flex-none w-[100px] border-r border-slate-200 text-xs text-slate-500 pt-1"
						>
							{{ ((i - 1) * 0.5).toFixed(1) }}s
						</div>
					</div>

					<div class="h-6 flex border-b border-slate-200 bg-white sticky top-6 z-0 relative">
						<div
							v-for="(scene, index) in shortsStore.script?.scenes"
							:key="index"
							class="absolute text-xs font-medium bg-orange-300 px-1 rounded"
							:style="{
								left: `${getSceneStartTime(index) * 200}px`,
								width: `${scene.duration * 200}px`
							}"
						>
							씬 {{ index + 1 }} ({{ scene.duration.toFixed(1) }}초)
						</div>
					</div>

					<div class="absolute top-0 bottom-0 w-0.5 bg-primary z-10" :style="{ left: `${shortsStore.currentTime * 200}px` }"></div>

					<div class="flex-1">
						<div class="h-10 border-b border-slate-200 bg-slate-50 relative"></div>

						<div class="h-10 border-b border-slate-200 bg-slate-50 relative">
							<div v-for="(scene, index) in shortsStore.script?.scenes" :key="index">
								<template v-if="scene.videoUrl">
									<div
										class="absolute h-full overflow-hidden rounded"
										:style="{
											left: `${getSceneStartTime(index) * 200}px`,
											width: `${scene.duration * 200}px`
										}"
									>
										<div
											v-for="time in Math.ceil(scene.duration * 2)"
											:key="`video-${index}-${time}`"
											class="absolute h-full bg-blue-200 rounded"
											:style="{
												left: `${(time - 1) * 0.5 * 200}px`,
												width: '100px'
											}"
										>
											<img :src="shortsStore.thumbnailCache[scene.videoUrl]" class="w-full h-full object-cover" />
										</div>
									</div>
								</template>
								<template v-else-if="scene.imageUrl">
									<div
										class="absolute h-full overflow-hidden rounded"
										:style="{
											left: `${getSceneStartTime(index) * 200}px`,
											width: `${scene.duration * 200}px`
										}"
									>
										<div
											v-for="time in Math.ceil(scene.duration * 2)"
											:key="`image-${index}-${time}`"
											class="absolute h-full bg-green-200 rounded"
											:style="{
												left: `${(time - 1) * 0.5 * 200}px`,
												width: '100px'
											}"
										>
											<img :src="scene.imageUrl" class="w-full h-full object-cover" alt="Scene image" />
										</div>
									</div>
								</template>
							</div>
						</div>

						<div class="h-10 border-b border-slate-200 bg-slate-50 relative">
							<div
								v-for="(scene, index) in shortsStore.script?.scenes"
								:key="index"
								class="absolute h-full bg-orange-200 rounded flex items-center justify-center"
								:style="{
									left: `${getSceneStartTime(index) * 200}px`,
									width: `${scene.duration * 200}px`
								}"
							>
								<span v-if="scene.voiceUrl" class="text-xs text-orange-800 font-medium">AI 음성 생성됨</span>
							</div>
						</div>

						<div class="h-10 border-b border-slate-200 bg-slate-50 relative">
							<div v-for="(scene, sceneIndex) in shortsStore.script?.scenes" :key="sceneIndex">
								<div
									v-for="(caption, captionIndex) in scene.captions"
									:key="captionIndex"
									class="absolute h-full bg-purple-200 rounded flex items-center justify-center"
									:style="{
										left: `${(getSceneStartTime(sceneIndex) + caption.startTime) * 200}px`,
										width: `${(caption.endTime - caption.startTime) * 200}px`
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
	</div>
</template>

<script setup lang="ts">
	const shortsStore = useShortsStore();
	const timelineRef = ref<HTMLElement | null>(null);
	const userInteracted = ref(false);
	const userInteractedTimeout = ref<NodeJS.Timeout | null>(null);

	const getSceneStartTime = (sceneIndex: number) => {
		if (!shortsStore.script?.scenes) return 0;
		return shortsStore.script.scenes.slice(0, sceneIndex).reduce((acc: number, scene: Scene) => acc + scene.duration, 0);
	};

	const handleWheel = (e: WheelEvent) => {
		e.preventDefault();
		const scrollableArea = e.currentTarget as HTMLElement;
		if (!scrollableArea) return;

		const scrollAmount = e.shiftKey ? e.deltaX : e.deltaY;
		scrollableArea.scrollLeft += scrollAmount;
	};

	const handleTimelineClick = (e: MouseEvent) => {
		const scrollableArea = e.currentTarget as HTMLElement;
		if (!scrollableArea) return;

		userInteracted.value = true;
		if (userInteractedTimeout.value) {
			clearTimeout(userInteractedTimeout.value);
		}
		userInteractedTimeout.value = setTimeout(() => {
			userInteracted.value = false;
		}, 2000);

		const rect = scrollableArea.getBoundingClientRect();
		const scrollLeft = scrollableArea.scrollLeft;
		const clickX = e.clientX - rect.left + scrollLeft;

		const newTime = clickX / 200;
		if (newTime >= 0 && newTime <= shortsStore.totalDuration) {
			shortsStore.seekVideo(newTime);
		}
	};

	watch(
		() => shortsStore.currentTime,
		(newTime) => {
			if (!timelineRef.value || userInteracted.value) return;

			const scrollableArea = timelineRef.value.querySelector('.overflow-x-auto') as HTMLElement;
			if (!scrollableArea) return;

			const timelineWidth = scrollableArea.clientWidth;
			const currentPosition = newTime * 200;

			scrollableArea.scrollTo({
				left: currentPosition - timelineWidth / 2
			});
		}
	);
</script>
