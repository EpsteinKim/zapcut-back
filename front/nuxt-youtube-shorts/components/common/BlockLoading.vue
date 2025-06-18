<template>
	<BlockUI :blocked="blocked" full-screen>
		<div v-if="blocked" class="fixed inset-0 flex flex-col items-center justify-center bg-black/10">
			<div class="relative w-[200px] h-[200px]">
				<svg class="w-[200px] h-[200px] animate-spin" viewBox="0 0 100 100">
					<defs>
						<linearGradient id="spinner-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
							<stop offset="0%" style="stop-color: #60a5fa" />
							<stop offset="50%" style="stop-color: #c084fc" />
							<stop offset="100%" style="stop-color: #f472b6" />
						</linearGradient>
						<filter id="glow">
							<feGaussianBlur stdDeviation="1.5" result="coloredBlur" />
							<feMerge>
								<feMergeNode in="coloredBlur" />
								<feMergeNode in="SourceGraphic" />
							</feMerge>
						</filter>
					</defs>
					<circle
						cx="50"
						cy="50"
						r="45"
						fill="none"
						stroke="url(#spinner-gradient)"
						stroke-width="8"
						stroke-linecap="round"
						stroke-dasharray="283"
						stroke-dashoffset="75"
						filter="url(#glow)"
					/>
				</svg>
			</div>
			<div v-if="text" class="mt-8 text-2xl font-medium text-white animate-pulse">
				<span
					class="text-transparent bg-clip-text bg-linear-to-r from-blue-400 via-purple-400 to-pink-400 animate-gradient-x hover:from-pink-400 hover:via-purple-400 hover:to-blue-400 transition-all duration-500"
				>
					{{ text }}
				</span>
			</div>
		</div>
	</BlockUI>
</template>

<script setup lang="ts">
	const blockLoadingStore = useBlockLoadingStore();
	const blocked = computed(() => blockLoadingStore.isBlocked);
	const text = computed(() => blockLoadingStore.text);
</script>

<style scoped>
	.animate-gradient-x {
		background-size: 200% 200%;
		animation: gradient-x 3s ease infinite;
	}

	@keyframes gradient-x {
		0% {
			background-position: 0% 50%;
		}
		50% {
			background-position: 100% 50%;
		}
		100% {
			background-position: 0% 50%;
		}
	}
</style>
