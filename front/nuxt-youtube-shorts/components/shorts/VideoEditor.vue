<template>
	<div>
		<!-- 헤더 -->
		<header class="flex justify-between items-center bg-surface-0">
			<div class="flex items-center space-x-4">
				<Button icon="pi pi-arrow-left" text @click="handleBack" />
				<h1 class="text-xl font-semibold" @click="console.log(shortsStore.getScript())">비디오 편집</h1>
			</div>
			<div class="flex items-center space-x-4">
				<Button label="임시 영상 생성" icon="pi pi-video" @click="createTempVideo" />
				<Button severity="help" label="영상 생성" icon="pi pi-video" @click="createVideo">
					{{ !shortsStore.videoUrl ? '영상 생성' : '이전으로' }}
				</Button>
				<Button label="저장" icon="pi pi-save" severity="primary" />
			</div>
		</header>

		<template v-if="!shortsStore.videoUrl">
			<Message v-if="!shortsStore.composedVideoUrl" severity="info" class="m-4" icon="pi pi-info-circle">
				영상까지 보고 싶으시다면 임시 영상을 만들어주세요
			</Message>
			<Message v-else-if="!shortsStore.videoUrl && shortsStore.composedVideoUrl" severity="info" class="m-4" icon="pi pi-info-circle">
				임시 영상입니다.
			</Message>
		</template>

		<div class="flex overflow-hidden">
			<!-- 좌측: 비디오 프리뷰 -->
			<div class="bg-surface-0 p-6 flex flex-col">
				<div class="w-[400px]">
					<!-- 비디오 프리뷰 -->
					<VideoPreview ref="videoPreviewRef" />
					<VideoControls class="mt-6" />

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
						<Tag severity="help" icon="pi pi-info-circle" value="Ctrl 또는 Command(⌘) 키를 누른 상태에서 타임라인을 클릭하세요" />
						<Tag severity="info" :value="`${formatTime(shortsStore.currentTime)} / ${formatTime(shortsStore.totalDuration)}`" />
					</div>
					<VideoTimeline />
				</div>

				<!-- 스크립트 & 음성 정보 -->
				<div class="flex-auto p-4">
					<ScriptSection :script="shortsStore.script" />
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
