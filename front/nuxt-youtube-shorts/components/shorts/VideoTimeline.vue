<template>
	<div ref="timelineRef" class="h-[200px] overflow-x-auto" @wheel="handleWheel">
		<!-- 전체 타임라인 컨테이너 -->
		<div
			class="relative inline-flex flex-col min-w-full cursor-pointer"
			:style="{ width: `${shortsStore.totalDuration * 200 + 100}px` }"
			@click="(e) => (e.ctrlKey || e.metaKey) && handleTimelineClick(e)"
		>
			<!-- 시간 눈금 -->
			<div class="h-6 flex sticky top-0 bg-white z-20">
				<!-- 라벨 영역만큼 빈 공간 -->
				<div class="sticky left-0 flex-none w-[100px] bg-white z-20"></div>
				<div class="flex">
					<div
						v-for="i in Math.ceil(shortsStore.totalDuration * 2)"
						:key="i"
						class="flex-none w-[100px] border-r border-slate-200 text-xs text-slate-500 pt-1"
					>
						{{ ((i - 1) * 0.5).toFixed(1) }}s
					</div>
				</div>
			</div>

			<!-- 씬 번호 표시 -->
			<div class="h-6 flex sticky top-6 bg-white z-20">
				<!-- 라벨 영역만큼 빈 공간 -->
				<div class="sticky left-0 flex-none w-[100px] bg-white z-20"></div>
				<div class="flex relative">
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
			</div>

			<!-- 현재 시간 커서 -->
			<div class="absolute top-0 bottom-0 w-0.5 bg-primary z-10" :style="{ left: `${100 + shortsStore.currentTime * 200}px` }"></div>

			<!-- 트랙 -->
			<div class="flex-1">
				<!-- 배경음악 트랙 -->
				<VideoTimelineTrack icon="volume-up" label="배경음악" type="bgm" />

				<!-- 영상 트랙 -->
				<VideoTimelineTrack icon="video" label="영상" type="video">
					<div v-for="(scene, index) in shortsStore.script?.scenes" :key="index">
						<!-- 비디오가 있는 경우 -->
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
						<!-- 이미지가 있는 경우 -->
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
				</VideoTimelineTrack>

				<!-- 음성 트랙 -->
				<VideoTimelineTrack icon="microphone" label="음성" type="voice">
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
				</VideoTimelineTrack>

				<!-- 자막 트랙 -->
				<VideoTimelineTrack icon="list" label="자막" type="caption">
					<div v-for="(scene, sceneIndex) in shortsStore.script?.scenes" :key="sceneIndex">
						<div
							v-for="(caption, captionIndex) in scene.captions"
							:key="captionIndex"
							class="absolute h-full bg-purple-200 rounded"
							:style="{
								left: `${(getSceneStartTime(sceneIndex) + caption.startTime) * 200}px`,
								width: `${(caption.endTime - caption.startTime) * 200}px`
							}"
						>
							<span class="text-xs px-1 truncate">{{ caption.text }}</span>
						</div>
					</div>
				</VideoTimelineTrack>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
	const shortsStore = useShortsStore();
	const timelineRef = ref<HTMLElement | null>(null);

	// 특정 씬의 시작 시간 계산
	const getSceneStartTime = (sceneIndex: number) => {
		if (!shortsStore.script?.scenes) return 0;
		return shortsStore.script.scenes.slice(0, sceneIndex).reduce((acc: number, scene: Scene) => acc + scene.duration, 0);
	};

	// 마우스 휠 이벤트 처리 (상하 스크롤을 좌우 스크롤로 변환)
	const handleWheel = (e: WheelEvent) => {
		e.preventDefault();
		if (!timelineRef.value) return;

		// Shift 키가 눌려있으면 좌우 스크롤, 아니면 상하 스크롤
		const scrollAmount = e.shiftKey ? e.deltaX : e.deltaY;
		timelineRef.value.scrollLeft += scrollAmount;
	};

	// 타임라인 클릭 이벤트 처리
	const handleTimelineClick = (e: MouseEvent) => {
		if (!timelineRef.value) return;

		const rect = timelineRef.value.getBoundingClientRect();
		const scrollLeft = timelineRef.value.scrollLeft;
		const clickX = e.clientX - rect.left + scrollLeft - 100; // 라벨 영역 너비(100px) 고려

		const newTime = clickX / 200; // 200px당 1초
		if (newTime >= 0 && newTime <= shortsStore.totalDuration) {
			if (shortsStore.videoElement) {
				shortsStore.videoElement.currentTime = newTime;
			}

			shortsStore.setCurrentTime(newTime);
		}
	};

	// 현재 시간이 변경될 때 자동 스크롤
	watch(
		() => shortsStore.currentTime,
		(newTime) => {
			if (!timelineRef.value) return;

			const timelineWidth = timelineRef.value.clientWidth;
			const currentPosition = newTime * 200 + 100; // 픽셀 단위 위치 (라벨 영역 고려)

			// 현재 시간 위치가 타임라인의 중앙에 오도록 스크롤
			timelineRef.value.scrollTo({
				left: currentPosition - timelineWidth / 2
			});
		}
	);
</script>
