export const useShortsStore = defineStore('shorts', () => {
	// 비디오 상태
	const videoUrl = ref<string>('');
	const setVideoUrl = (url: string) => {
		videoUrl.value = url;
	};
	const currentTime = ref(0);

	const setCurrentTime = (time: number) => {
		currentTime.value = time;
	};
	const duration = ref(0);
	const setDuration = (time: number) => {
		duration.value = time;
	};
	const isPlaying = ref(false);
	const setIsPlaying = (bool: boolean) => {
		isPlaying.value = bool;
	};
	const isMuted = ref(false);
	const setIsMuted = (bool: boolean) => {
		isMuted.value = bool;
	};
	const playbackSpeed = ref(1);
	// 스크립트 상태
	const script = ref<ShortsScript | null>(null);
	const setScript = async (newScript: ShortsScript | null) => {
		if (newScript && !videoUrl.value) {
			if (!script.value || isAudioChanged(script.value, newScript)) {
				const { composeScriptAudio } = useAudioComposer();
				composedAudio.value = await composeScriptAudio(newScript);
			}
		}

		script.value = JSON.parse(JSON.stringify(newScript));
	};
	const getScript = () => {
		return script.value ? JSON.parse(JSON.stringify(script.value)) : null;
	};
	const setPlaybackSpeed = (speed: number) => {
		playbackSpeed.value = speed;
	};

	const sceneEditDialogVisible = ref(false);
	const setSceneEditDialogVisible = (visible: boolean) => {
		sceneEditDialogVisible.value = visible;
	};

	const targetSceneIndex = ref(-1);
	const setTargetSceneIndex = (index: number) => {
		targetSceneIndex.value = index;
	};

	const videoElement = ref<HTMLVideoElement | null>(null);
	const setVideoElement = (element: HTMLVideoElement | null) => {
		videoElement.value = element;
	};

	const thumbnailCache = ref<Record<string, string>>({});

	const seekVideo = (time: number) => {
		currentTime.value = time;
		if (videoElement.value) {
			videoElement.value.currentTime = time;
		}

		if (!videoUrl.value) {
			if (isPlaying.value) {
				composedAudio.value?.play(time, playbackSpeed.value);
			}
		}
	};

	const currentScene = computed(() => {
		if (!script.value) return null;

		let accumulatedTime = 0;
		for (const scene of script.value.scenes) {
			if (currentTime.value >= accumulatedTime && currentTime.value < accumulatedTime + scene.duration) {
				return scene;
			}
			accumulatedTime += scene.duration;
		}
		return null;
	});

	// 현재 시간에 해당하는 자막 찾기
	const currentCaptions = computed(() => {
		if (!currentScene.value) return [];

		const sceneStartTime =
			script.value?.scenes.slice(0, script.value.scenes.indexOf(currentScene.value)).reduce((acc, scene) => acc + scene.duration, 0) || 0;
		const sceneTime = currentTime.value - sceneStartTime;

		return currentScene.value.captions.filter((caption) => sceneTime >= caption.startTime && sceneTime <= caption.endTime);
	});

	// 오디오 관련 상태
	const composedAudio = ref<ComposedAudio | null>(null);
	const composedVideoUrl = ref<string | null>(null);

	// 총 영상 길이 계산
	const totalDuration = computed(() => {
		return script.value?.scenes.reduce((acc, scene) => acc + scene.duration, 0) || 0;
	});

	// Reset 함수 추가
	const reset = () => {
		videoUrl.value = '';
		currentTime.value = 0;
		duration.value = 0;
		isPlaying.value = false;
		isMuted.value = false;
		playbackSpeed.value = 1;
		script.value = null;
		videoElement.value = null;
		sceneEditDialogVisible.value = false;
		targetSceneIndex.value = -1;

		// 오디오 관련 초기화
		if (composedAudio.value) {
			composedAudio.value.stop();
			composedAudio.value = null;
		}
		if (composedVideoUrl.value) {
			URL.revokeObjectURL(composedVideoUrl.value);
			composedVideoUrl.value = null;
		}
	};

	return {
		script,
		setScript,
		getScript,
		videoUrl,
		setVideoUrl,
		currentTime,
		setCurrentTime,
		duration,
		setDuration,
		isPlaying,
		setIsPlaying,
		isMuted,
		setIsMuted,
		playbackSpeed,
		setPlaybackSpeed,
		totalDuration,
		videoElement,
		setVideoElement,
		sceneEditDialogVisible,
		setSceneEditDialogVisible,
		targetSceneIndex,
		setTargetSceneIndex,
		thumbnailCache,
		seekVideo,
		currentScene,
		currentCaptions,
		composedAudio,
		composedVideoUrl,
		reset
	};
});

const isAudioChanged = (oldScript: ShortsScript, newScript: ShortsScript) => {
	const oldScenes = oldScript.scenes.map((scene) => ({
		voiceUrl: scene.voiceUrl || null
	}));
	const newScenes = newScript.scenes.map((scene) => ({
		voiceUrl: scene.voiceUrl || null
	}));
	return JSON.stringify(oldScenes) !== JSON.stringify(newScenes);
};
