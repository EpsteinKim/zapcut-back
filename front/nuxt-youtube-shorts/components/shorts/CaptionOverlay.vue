<template>
	<div class="absolute inset-0 flex flex-col items-center justify-center">
		<div
			class="text-white text-center max-w-[90%] [filter:drop-shadow(0_0_0.7px_#000)_drop-shadow(0_0_0.7px_#000)_drop-shadow(0_0_0.7px_#000)_drop-shadow(0_0_0.7px_#000)_drop-shadow(0_0_0.7px_#000)_drop-shadow(0_0_0.7px_#000)_drop-shadow(0_0_0.7px_#000)_drop-shadow(0_0_0.7px_#000)]"
		>
			<template v-for="(caption, index) in captions" :key="index">
				<div class="font-bold font-Jua-Regular" :style="{ fontSize: '9.26cqw', marginBottom: '1.85cqw' }">
					{{ caption.text }}
				</div>
			</template>
		</div>
	</div>
</template>

<script setup lang="ts">
	interface Caption {
		text: string;
	}

	interface Props {
		captions: Caption[];
	}

	defineProps<Props>();
</script>
