<template>
	<div>
		<!-- 헤더 -->
		<header class="flex flex-col md:flex-row justify-between items-start md:items-center bg-surface-0 p-3 md:p-4 gap-3 md:gap-0">
			<div class="flex items-center space-x-4">
				<Button icon="pi pi-arrow-left" text size="small" @click="handleBack" />
				<h1
					class="text-lg md:text-xl font-semibold"
					@click="
						console.log(shortsStore.getScript());
						console.log(shortsStore.currentTime);
					"
				>
					비디오 편집
				</h1>
			</div>
			<div class="flex flex-wrap items-center gap-2 md:space-x-4 w-full md:w-auto">
				<Button label="임시 영상" size="small" icon="pi pi-video" class="flex-1 md:flex-none" @click="createTempVideo" />
				<Button
					severity="help"
					size="small"
					:label="!shortsStore.videoUrl ? '영상 생성' : '이전으로'"
					icon="pi pi-video"
					class="flex-1 md:flex-none"
					@click="createVideo"
				/>
				<Button label="저장" size="small" icon="pi pi-save" severity="primary" class="flex-1 md:flex-none" />
			</div>
		</header>

		<template v-if="!shortsStore.videoUrl">
			<Message v-if="!shortsStore.composedVideoUrl" severity="info" size="small" class="my-3 mx-3" icon="pi pi-info-circle">
				영상까지 보고 싶으시다면 임시 영상을 만들어주세요
			</Message>
			<Message v-else-if="!shortsStore.videoUrl && shortsStore.composedVideoUrl" severity="info" size="small" class="my-3 mx-3" icon="pi pi-info-circle">
				임시 영상입니다.
			</Message>
		</template>

		<div class="flex flex-col lg:flex-row overflow-hidden">
			<!-- 모바일에서는 상단, 데스크톱에서는 좌측: 비디오 프리뷰 -->
			<div class="w-full lg:w-6/23 mx-2 mb-4 lg:mb-0">
				<!-- 비디오 프리뷰 -->
				<div class="max-w-sm mx-auto lg:max-w-none">
					<VideoPreview ref="videoPreviewRef" />
					<VideoControls class="mt-4 lg:mt-6" />
				</div>

				<Divider class="my-4 lg:my-6" />

				<div class="text-center text-xs md:text-sm text-slate-500">
					<i class="pi pi-info-circle mr-2"></i>
					{{ shortsStore.script?.title }}
				</div>
			</div>

			<!-- 모바일에서는 하단, 데스크톱에서는 우측: 타임라인과 스크립트 -->
			<div class="w-full lg:w-17/23 mx-2">
				<div class="flex flex-col overflow-hidden">
					<VideoTimeline class="my-2" />
					<ScriptSection class="my-2" :script="shortsStore.script" />
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
	const api = useApi();
	const shortsStore = useShortsStore();
	const { showMessage } = useMessageToast();
	const blockLoadingStore = useBlockLoadingStore();
	const { getComposedVideoBlob } = useVideoComposer();

	const handleBack = () => {
		shortsStore.reset();
	};

	const createTempVideo = async () => {
		const script = shortsStore.getScript();
		if (shortsStore.composedVideoUrl) {
			URL.revokeObjectURL(shortsStore.composedVideoUrl);
			shortsStore.composedVideoUrl = null;
		}
		const composedVideoBlob = await getComposedVideoBlob(script);
		shortsStore.composedVideoUrl = URL.createObjectURL(composedVideoBlob);
	};

	const createVideo = async () => {
		if (shortsStore.videoUrl) {
			shortsStore.setVideoUrl('');
			return;
		}
		blockLoadingStore.setBlocked(true, '모든 선택사항을 반영한 영상을 생성중입니다...');
		try {
			const request: ShortsVideoRequest = {
				...shortsStore.getScript(),
				backgroundMusicUrl: undefined
			};
			const videoUrl = await api.shorts.generateVideo(request);
			if (videoUrl) {
				shortsStore.setVideoUrl(videoUrl);
				showMessage('영상 생성 완료', 'success');
			} else {
				showMessage('영상 생성 실패', 'error');
			}
		} catch (e) {
			showMessage('영상 생성 실패' + getErrorMessage(e), 'error');
		} finally {
			blockLoadingStore.setBlocked(false);
		}
	};

	watch(
		() => shortsStore.videoUrl,
		(newVideoUrl) => {
			if (!newVideoUrl) {
				shortsStore.setDuration(shortsStore.totalDuration);
			}
		}
	);
</script>
