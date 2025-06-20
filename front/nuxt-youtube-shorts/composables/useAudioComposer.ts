import type { ShortsScript, Scene } from '~/types/api';

export const useAudioComposer = () => {
	const blockLoadingStore = useBlockLoadingStore();
	const audioContext = ref<AudioContext | null>(null);
	const sourceNode = ref<AudioBufferSourceNode | null>(null);
	const gainNode = ref<GainNode | null>(null);

	const initializeAudioContext = () => {
		if (!audioContext.value) {
			audioContext.value = new AudioContext();
			gainNode.value = audioContext.value.createGain();
			gainNode.value.connect(audioContext.value.destination);
		}
	};

	const loadAudioBuffer = async (url: string): Promise<AudioBuffer> => {
		if (!audioContext.value) initializeAudioContext();

		const response = await fetch(url);
		const arrayBuffer = await response.arrayBuffer();
		return await audioContext.value!.decodeAudioData(arrayBuffer);
	};

	const composeScriptAudio = async (script: ShortsScript) => {
		if (!audioContext.value) initializeAudioContext();

		blockLoadingStore.setBlocked(true, '오디오 합성 작업중...');
		const totalDuration = script.scenes.reduce((acc, scene) => acc + scene.duration, 0);

		const offlineContext = new OfflineAudioContext(2, audioContext.value!.sampleRate * totalDuration, audioContext.value!.sampleRate);

		if (script.backgroundMusicUrl) {
			const backgroundMusicBuffer = await loadAudioBuffer(script.backgroundMusicUrl);
			const backgroundMusicSourceNode = offlineContext.createBufferSource();
			backgroundMusicSourceNode.buffer = backgroundMusicBuffer;
			backgroundMusicSourceNode.connect(offlineContext.destination);
			backgroundMusicSourceNode.start(0, 0, totalDuration);
		}

		let currentTime = 0;
		for (const scene of script.scenes) {
			if (!scene.voiceUrl) {
				currentTime += scene.duration;
				continue;
			}

			try {
				const audioBuffer = await loadAudioBuffer(scene.voiceUrl);

				const sourceNode = offlineContext.createBufferSource();
				sourceNode.buffer = audioBuffer;

				const gainNode = offlineContext.createGain();
				gainNode.gain.value = 1;

				sourceNode.connect(gainNode);
				gainNode.connect(offlineContext.destination);
				sourceNode.start(currentTime);

				currentTime += scene.duration;
			} catch (error) {
				console.error('오디오 로드 실패:', error);
				currentTime += scene.duration;
			}
		}

		const renderedBuffer = await offlineContext.startRendering();

		blockLoadingStore.setBlocked(false);

		return {
			buffer: renderedBuffer,
			duration: totalDuration,
			play: (startTime = 0, playbackRate = 1) => {
				if (!audioContext.value) initializeAudioContext();

				if (sourceNode.value) {
					sourceNode.value.stop();
					sourceNode.value.disconnect();
				}

				sourceNode.value = audioContext.value!.createBufferSource();
				sourceNode.value.buffer = renderedBuffer;
				sourceNode.value.playbackRate.value = playbackRate;
				if (!gainNode.value) {
					gainNode.value = audioContext.value!.createGain();
				}
				sourceNode.value.connect(gainNode.value);
				gainNode.value.connect(audioContext.value!.destination);

				sourceNode.value.start(0, startTime);
			},
			stop: () => {
				if (sourceNode.value) {
					sourceNode.value.stop();
					sourceNode.value.disconnect();
					sourceNode.value = null;
				}
			},
			setVolume: (volume: number) => {
				if (gainNode.value) {
					gainNode.value.gain.value = volume;
				}
			},
			cleanup: () => {
				if (sourceNode.value) {
					sourceNode.value.stop();
					sourceNode.value.disconnect();
					sourceNode.value = null;
				}

				if (audioContext.value) {
					audioContext.value.close();
					audioContext.value = null;
				}
			}
		};
	};

	return { composeScriptAudio };
};

export interface ComposedAudio {
	buffer: AudioBuffer;
	duration: number;
	play: (startTime?: number, playbackRate?: number) => void;
	stop: () => void;
	setVolume: (volume: number) => void;
	cleanup: () => void;
}
