<template>
	<div class="mb-4">
		<div class="flex justify-between items-center align-middle mb-4">
			<div class="flex items-center gap-2">
				<h3 class="text-lg pl-2 font-semibold">생성된 스크립트 & 음성</h3>
				<!-- <Button
					label="음성 일괄 생성"
					icon="pi pi-volume-up"
					severity="help"
					size="small"
					:loading="state.isGeneratingVoice"
					:disabled="state.isGeneratingVoice"
					@click="generateVoice"
				/> -->
			</div>

			<Tag icon="pi pi-clock" severity="info" :value="`${shortsStore.totalDuration.toFixed(1)}초`" class="mr-2" />
		</div>
		<div class="bg-surface-0 rounded-lg">
			<div class="space-y-4 overflow-y-auto max-h-[550px] min-h-[200px]">
				<div
					v-for="(scene, index) in shortsStore.script?.scenes"
					:key="index"
					class="p-4 bg-surface-50 rounded-lg hover:bg-surface-100 transition-colors"
					:class="{ 'opacity-50': state.isGeneratingVoice && state.generatingSceneIndex !== index }"
				>
					<div class="flex flex-col gap-3">
						<div class="flex flex-wrap items-start justify-between gap-2">
							<div class="flex flex-col gap-2 w-full">
								<div class="flex items-center justify-between">
									<div class="flex items-center gap-2">
										<span class="font-medium text-lg">씬 {{ index + 1 }}</span>
										<Tag :value="`${scene.duration.toFixed(1)}초`" />
									</div>
									<div class="flex items-center gap-2">
										<MediaUpload :src="scene.videoUrl || scene.imageUrl" @upload-complete="uploadImageComplete(index, $event)">
											<Button v-tooltip="'파일 업로드'" icon="pi pi-image" text severity="info" />
										</MediaUpload>
										<Button
											v-if="!scene.voiceUrl"
											v-tooltip="'음성 생성'"
											icon="pi pi-volume-up"
											text
											severity="help"
											:loading="state.generatingScenes.has(index)"
											:disabled="state.isGeneratingVoice"
											@click="generateVoiceForScene(index)"
										/>
										<Button
											v-tooltip="'씬 수정'"
											icon="pi pi-pencil"
											text
											severity="secondary"
											:disabled="state.isGeneratingVoice"
											@click.stop="openSceneEditDialog(index)"
										/>
										<Button
											v-tooltip="'씬 삭제'"
											icon="pi pi-trash"
											text
											severity="danger"
											:disabled="state.isGeneratingVoice"
											@click="deleteScene(index)"
										/>
									</div>
								</div>
								<Tag v-if="scene.description" :value="scene.description" severity="info" class="w-full" />
							</div>
						</div>

						<div class="bg-surface-0 rounded p-3">
							<div class="space-y-2">
								<div v-for="(caption, cIndex) in scene.captions" :key="cIndex" class="flex items-center justify-between text-sm">
									<span class="flex-1 pr-4">{{ caption.text }}</span>
									<span class="text-slate-500 whitespace-nowrap">
										{{ caption.startTime.toFixed(1) }}s - {{ caption.endTime.toFixed(1) }}s
									</span>
								</div>
							</div>
						</div>

						<div v-if="scene.voiceUrl" class="flex justify-end">
							<Tag
								value="AI 음성 듣기"
								severity="success"
								class="cursor-pointer hover:bg-green-100 transition-colors"
								@click="playVoice(scene.voiceUrl)"
							>
								<template #icon>
									<i class="pi pi-volume-up"></i>
								</template>
							</Tag>
						</div>

						<!-- 로딩 인디케이터 -->
						<div v-if="state.generatingScenes.has(index)" class="mt-2">
							<ProgressBar mode="indeterminate" class="h-1" />
						</div>
					</div>
				</div>
			</div>
		</div>
		<SceneEditDialog />
	</div>
</template>

<script setup lang="ts">
	import { useConfirm } from 'primevue/useconfirm';

	const confirm = useConfirm();
	const shortsStore = useShortsStore();
	const api = useApi();
	const { showMessage } = useMessageToast();

	const state = reactive({
		isGeneratingVoice: false,
		generatingSceneIndex: -1,
		generatingScenes: new Set<number>()
	});

	const openSceneEditDialog = (index: number) => {
		shortsStore.setTargetSceneIndex(index);
		shortsStore.setSceneEditDialogVisible(true);
	};

	// 씬 삭제
	const deleteScene = (index: number) => {
		confirm.require({
			message: '이 씬을 삭제하시겠습니까?',
			header: '씬 삭제 확인',
			icon: 'pi pi-exclamation-triangle',
			accept: () => {
				if (!shortsStore.script) return;

				const updatedScript = { ...shortsStore.script };
				updatedScript.scenes = updatedScript.scenes.filter((_, i) => i !== index);
				shortsStore.setScript(updatedScript);
			}
		});
	};

	// 음성 재생
	const playVoice = (url: string) => {
		const audio = new Audio(url);
		audio.play();
	};

	// 씬 음성 생성
	const generateVoiceForScene = async (sceneIndex: number) => {
		if (!shortsStore.script) return;

		state.isGeneratingVoice = true;
		state.generatingSceneIndex = sceneIndex;
		state.generatingScenes.add(sceneIndex);

		try {
			const scene = shortsStore.script.scenes[sceneIndex];
			const text = scene.captions.map((c) => c.text).join(' ');
			const voiceUrl = await api.shorts.generateVoice(text, scene.duration);

			const updatedScript = { ...shortsStore.script };
			updatedScript.scenes[sceneIndex] = {
				...scene,
				voiceUrl
			};

			shortsStore.setScript(updatedScript);
			showMessage(`씬 ${sceneIndex + 1} 음성 생성이 완료되었습니다`, 'success');
		} catch (e) {
			showMessage(`씬 ${sceneIndex + 1} 음성 생성에 실패했습니다: ${getErrorMessage(e)}`, 'error');
		} finally {
			state.isGeneratingVoice = false;
			state.generatingSceneIndex = -1;
			state.generatingScenes.delete(sceneIndex);
		}
	};

	// 전체 음성 생성
	const generateVoice = async () => {
		if (!shortsStore.script) return;

		state.isGeneratingVoice = true;
		try {
			const updatedScript = { ...shortsStore.script };
			const promises: Promise<void>[] = [];

			for (let i = 0; i < updatedScript.scenes.length; i++) {
				const scene = updatedScript.scenes[i];
				// 이미 음성이 있거나 생성 중인 씬은 건너뛰기
				if (scene.voiceUrl || state.generatingScenes.has(i)) continue;

				state.generatingScenes.add(i);
				const promise = (async () => {
					try {
						const text = scene.captions.map((c) => c.text).join(' ');
						const voiceUrl = await api.shorts.generateVoice(text, scene.duration);
						updatedScript.scenes[i] = {
							...scene,
							voiceUrl
						};
					} catch (e) {
						console.error(`씬 ${i + 1} 음성 생성 실패:`, e);
					} finally {
						state.generatingScenes.delete(i);
					}
				})();
				promises.push(promise);
			}

			await Promise.all(promises);
			shortsStore.setScript(updatedScript);
			showMessage('음성 생성이 완료되었습니다', 'success');
		} catch (e) {
			showMessage('음성 생성에 실패했습니다: ' + getErrorMessage(e), 'error');
		} finally {
			state.isGeneratingVoice = false;
		}
	};

	const uploadImageComplete = (index: number, url: string) => {
		if (!shortsStore.script) return;

		const scene = shortsStore.script.scenes[index];
		if (scene) {
			scene.imageUrl = url;
			shortsStore.setScript({ ...shortsStore.script });
		}
	};
</script>

<style scoped>
	.pi-volume-up {
		transition: all 0.2s ease;
	}

	.cursor-pointer:hover .pi-volume-up {
		transform: scale(1.1);
	}
</style>
