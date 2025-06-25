<template>
	<div class="absolute inset-0 flex flex-col items-center justify-center">
		<div
			class="text-white text-center max-w-[90%] [filter:drop-shadow(0_0_0.6px_#000)_drop-shadow(0_0_0.6px_#000)_drop-shadow(0_0_0.6px_#000)_drop-shadow(0_0_0.6px_#000)_drop-shadow(0_0_0.6px_#000)_drop-shadow(0_0_0.6px_#000)_drop-shadow(0_0_0.6px_#000)_drop-shadow(0_0_0.6px_#000)]"
		>
			<template v-for="(caption, index) in shortsStore.currentCaptions" :key="index">
				<div class="font-bold font-Jua-Regular" :class="getCaptionClasses(caption)" :style="getCaptionStyle(caption)">
					<template v-if="caption.animationEffect === CaptionAnimationEffect.SEQUENTIAL">
						<div class="text-center">
							{{ getAnimatedText(caption) }}
						</div>
					</template>
					<template v-else>
						{{ caption.text }}
					</template>
				</div>
			</template>
		</div>
	</div>
</template>

<script setup lang="ts">
	const shortsStore = useShortsStore();

	// 애니메이션별 텍스트 렌더링 함수들
	const animationRenderers: Record<string, (caption: CaptionInfo) => string> = {
		[CaptionAnimationEffect.SEQUENTIAL]: (caption: CaptionInfo) => {
			const currentSceneStartTime =
				shortsStore.script?.scenes
					.slice(0, shortsStore.script.scenes.indexOf(shortsStore.currentScene!))
					.reduce((acc, scene) => acc + scene.duration, 0) || 0;

			const sceneTime = shortsStore.currentTime - currentSceneStartTime;
			const captionDuration = caption.endTime - caption.startTime;
			const elapsed = sceneTime - caption.startTime;

			// 애니메이션은 지속시간에서 0.2초를 뺀 시간 동안 진행
			const animationDuration = Math.max(0.1, captionDuration - 0.2);

			const isStarted = elapsed > 0;
			const isCompleted = elapsed >= animationDuration;

			if (!isStarted) return '';
			if (isCompleted) return caption.text;

			// 24fps에서 2프레임씩 진행 = 12fps 업데이트
			const frameInterval = 1 / 12;
			const totalFrames = Math.floor(animationDuration / frameInterval);
			const currentFrame = Math.floor(elapsed / frameInterval);

			const charsPerFrame = Math.max(1, Math.ceil(caption.text.length / totalFrames));
			const targetLength = Math.min(caption.text.length, currentFrame * charsPerFrame);

			return caption.text.substring(0, targetLength);
		},
		default: (caption: CaptionInfo) => caption.text
	};

	// 애니메이션에 따른 텍스트 반환
	const getAnimatedText = (caption: CaptionInfo) => {
		const renderer = animationRenderers[caption.animationEffect || 'default'] || animationRenderers.default;
		return renderer(caption);
	};

	// 자막 클래스 생성
	const getCaptionClasses = (caption: CaptionInfo) => {
		const classes = [];

		if (caption.animationEffect === CaptionAnimationEffect.SMOOTH_POP) {
			classes.push('animate-smooth-pop');
		}
		if (caption.animationEffect === CaptionAnimationEffect.LARGE_TEXT) {
			classes.push('animate-large-text');
		}

		return classes.join(' ');
	};

	// 자막 스타일 생성
	const getCaptionStyle = (caption: CaptionInfo) => {
		const style: Record<string, string> = {
			fontSize: '9.26cqw',
			marginBottom: '1.85cqw'
		};

		console.log(caption);
		if (caption.color) {
			style.color = caption.color;
		}

		return style;
	};
</script>

<style scoped>
	@keyframes smooth-pop {
		0% {
			transform: scale(0.8);
		}
		50% {
			transform: scale(1.1);
		}
		100% {
			transform: scale(1);
		}
	}

	@keyframes large-text {
		0% {
			transform: scale(0.8);
		}
		100% {
			transform: scale(1.3);
		}
	}

	.animate-smooth-pop {
		animation: smooth-pop 0.2s ease-out;
	}

	.animate-large-text {
		animation: large-text 0.2s linear forwards;
	}
</style>
