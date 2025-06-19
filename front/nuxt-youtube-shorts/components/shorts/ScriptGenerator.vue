<template>
	<div class="p-6 max-w-screen-md mx-auto">
		<div class="mb-6">
			<h2 class="text-2xl font-bold mb-4" @click="console.log(initialValues)">비디오 스크립트 생성</h2>
			<Card class="w-full">
				<template #title>
					<div class="flex items-center gap-2">
						<i class="pi pi-file-edit text-xl"></i>
						<span class="text-xl font-semibold">스크립트 생성</span>
					</div>
				</template>
				<template #content>
					<Form v-slot="$form" :resolver="resolver" :initial-values="initialValues" class="space-y-4" @submit="onFormSubmit">
						<div class="flex flex-col gap-1">
							<label class="block mb-2 font-medium">
								쇼츠 요청 사항
								<span class="text-red-500 ml-1">(필수)</span>
							</label>
							<div class="relative">
								<Textarea name="description" class="w-full" rows="4" auto-resize max-length="1000" fluid />
								<div class="absolute bottom-2 right-2 text-sm text-gray-500">{{ $form.description?.value?.length || 0 }}/1000</div>
							</div>
							<Message v-if="$form.description?.invalid" severity="error" size="small" variant="simple">
								{{ $form.description.error?.message }}
							</Message>
						</div>

						<div class="flex gap-5">
							<div class="flex flex-col gap-1 flex-1">
								<label class="block mb-2 font-medium">제목</label>
								<InputText name="title" class="w-full" type="text" fluid />
								<Message v-if="$form.title?.invalid" severity="error" size="small" variant="simple">{{ $form.title.error?.message }}</Message>
							</div>
							<div class="flex flex-col gap-1 flex-1">
								<label class="block mb-2 font-medium">영상 길이 (초)</label>
								<Dropdown name="duration" :options="[30, 60]" class="w-full" fluid />
								<Message v-if="$form.duration?.invalid" severity="error" size="small" variant="simple">
									{{ $form.duration.error?.message }}
								</Message>
							</div>
						</div>

						<div class="flex gap-5">
							<div class="flex flex-col gap-1 flex-1">
								<label class="block mb-2 font-medium">이미지 혹은 영상</label>
								<div class="flex flex-wrap gap-2">
									<div
										v-for="(media, index) in mediaList"
										:key="index"
										class="relative w-[120px] h-[120px] rounded-lg overflow-hidden border border-gray-200"
									>
										<template v-if="media.type === 'video'">
											<video :src="media.url" class="w-full h-full object-cover" />
										</template>
										<template v-else-if="media.type === 'image'">
											<img :src="media.url" class="w-full h-full object-cover" alt="Media preview" />
										</template>
										<button
											class="absolute top-1 right-1 w-6 h-6 bg-black/50 rounded-full flex items-center justify-center text-white hover:bg-black/70"
											@click="removeMedia(index)"
										>
											<i class="pi pi-times"></i>
										</button>
									</div>
									<MediaUpload
										:allowed-types="['video', 'image']"
										:max-file-size="20"
										:allow-dialog="false"
										:allow-multiple="true"
										@upload-complete="addMedia"
										@upload-progress="(percent: number) => (state.uploadProgress = percent)"
										@upload-state-change="(uploadState: 'start' | 'end') => (state.isUploading = uploadState === 'start')"
									>
										<div
											class="w-[120px] h-[120px] rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center text-gray-300 hover:border-gray-400 hover:text-gray-400 cursor-pointer flex-col"
										>
											<i class="pi pi-plus text-2xl"></i>
											<div class="text-sm">Drag & Drop</div>
											<div v-if="state.isUploading" class="absolute inset-0 flex items-center justify-center bg-black/50 rounded-lg">
												<div class="w-16 h-16 relative">
													<ProgressSpinner style="width: 100%; height: 100%" stroke-width="4" />
													<div class="absolute inset-0 flex items-center justify-center text-white text-sm">
														{{ state.uploadProgress }}%
													</div>
												</div>
											</div>
										</div>
									</MediaUpload>
								</div>
							</div>
							<!-- <div class="flex flex-col gap-1 flex-1">
								<label class="block mb-2 font-medium">배경 음악</label>
								<div class="flex flex-wrap gap-2">
									<div v-if="backgroundMusicUrl" class="flex items-center justify-center gap-4 w-full">
										<audio :src="backgroundMusicUrl" controls preload="metadata" class="z-0"></audio>
										<Button severity="danger" size="small" icon="pi pi-times" @click="backgroundMusicUrl = ''" />
									</div>
									<MediaUpload
										v-if="!backgroundMusicUrl"
										:allowed-types="['audio']"
										:max-file-size="20"
										:allow-dialog="false"
										@upload-complete="(url: string) => (backgroundMusicUrl = url)"
										@upload-progress="(percent: number) => (state.uploadProgress = percent)"
										@upload-state-change="(uploadState: 'start' | 'end') => (state.isUploading = uploadState === 'start')"
									>
										<div
											class="w-[120px] h-[120px] rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center text-gray-300 hover:border-gray-400 hover:text-gray-400 cursor-pointer flex-col"
										>
											<i class="pi pi-plus text-2xl"></i>
											<div class="text-sm">Drag & Drop</div>
											<div v-if="state.isUploading" class="absolute inset-0 flex items-center justify-center bg-black/50 rounded-lg">
												<div class="w-16 h-16 relative">
													<ProgressSpinner style="width: 100%; height: 100%" stroke-width="4" />
													<div class="absolute inset-0 flex items-center justify-center text-white text-sm">
														{{ state.uploadProgress }}%
													</div>
												</div>
											</div>
										</div>
									</MediaUpload>
								</div>
							</div> -->
						</div>

						<div class="flex justify-end mt-4">
							<Button type="submit" label="스크립트 생성" icon="pi pi-check" />
						</div>
					</Form>
				</template>
			</Card>
		</div>

		<template v-if="shortsStore.script">
			<ScriptSection />
			<Button severity="success" label="해당 스크립트로 진행하기" class="w-full" @click="shortsStore.setScript(shortsStore.script)" />
		</template>

		<div v-if="state.error" class="mt-4 p-4 bg-red-100 text-red-700 rounded">
			{{ state.error }}
		</div>
	</div>
</template>

<script setup lang="ts">
	import { ref } from 'vue';
	import { zodResolver } from '@primevue/forms/resolvers/zod';
	import { z } from 'zod';

	interface FormValues {
		duration: number;
		title: string;
		description: string;
	}
	const initialValues = ref<FormValues>({
		duration: 30,
		title: '',
		description: ''
	});

	const api = useApi();
	const shortsStore = useShortsStore();
	const toast = useToast();
	const blockLoadingStore = useBlockLoadingStore();
	const state = reactive({
		error: '',
		uploadProgress: 0,
		isUploading: false
	});

	const mediaList = ref<Array<{ url: string; type: 'image' | 'video' }>>([]);
	const backgroundMusicUrl = ref<string>('');

	const resolver = ref(
		zodResolver(
			z.object({
				title: z.string().optional(),
				description: z.string().min(5, { message: '최소 5글자는 입력해야 합니다.' }).max(1000, { message: '설명은 1000자를 초과할 수 없습니다' }),
				duration: z.number().min(1, { message: '영상 길이를 선택해주세요' })
			})
		)
	);

	const onFormSubmit = async ({ valid, values }: { valid: boolean; values: FormValues }) => {
		if (!valid) return;

		try {
			blockLoadingStore.setBlocked(true, 'AI가 영상 스크립트를 생성중입니다...');

			const generatedScript = await api.shorts.generateScript({
				url: values.url,
				duration: values.duration,
				title: values.title,
				description: values.description
			});

			if (!generatedScript) {
				throw '스크립트 생성에 실패했습니다.';
			}

			blockLoadingStore.setBlocked(true, 'AI가 음성을 생성중입니다...');

			for (const scene of generatedScript.scenes) {
				const voiceUrl = await api.shorts.generateVoice(scene.captions.map((caption) => caption.text).join(' '), scene.duration);
				scene.voiceUrl = voiceUrl;
			}

			blockLoadingStore.setBlocked(true, '사용자의 비디오 혹은 이미지를 추가중입니다...');
			if (mediaList.value.length > 0) {
				for (const [index, media] of mediaList.value.entries()) {
					if (generatedScript.scenes.at(index)) {
						if (media.type === 'video') {
							generatedScript.scenes[index].videoUrl = media.url;
						} else {
							generatedScript.scenes[index].imageUrl = media.url;
						}
					}
				}
			}

			blockLoadingStore.setBlocked(true, '비디오 썸네일을 생성중입니다...');
			for (const scene of generatedScript.scenes) {
				if (scene.videoUrl) {
					const video = document.createElement('video');
					video.src = scene.videoUrl;
					video.preload = 'metadata';

					await new Promise((resolve) => {
						video.onloadedmetadata = () => {
							video.currentTime = 0;
							resolve(null);
						};
					});

					const canvas = document.createElement('canvas');
					canvas.width = video.videoWidth;
					canvas.height = video.videoHeight;
					const ctx = canvas.getContext('2d');
					ctx?.drawImage(video, 0, 0, canvas.width, canvas.height);
					shortsStore.thumbnailCache[scene.videoUrl] = canvas.toDataURL('image/jpeg');
				}
			}

			if (backgroundMusicUrl.value) {
				generatedScript.backgroundMusicUrl = backgroundMusicUrl.value;
			}

			shortsStore.setScript(generatedScript);
		} catch (e) {
			state.error = e instanceof Error ? e.message : '예상치 못한 오류가 발생했습니다.';
			toast.add({ severity: 'error', summary: state.error, life: 3000 });
		} finally {
			blockLoadingStore.setBlocked(false);
		}
	};

	const addMedia = (url: string) => {
		const type = url.match(/\.(mp4|webm|ogg)$/i) ? 'video' : 'image';
		mediaList.value.push({ url, type });
	};

	const removeMedia = (index: number) => {
		mediaList.value.splice(index, 1);
	};
</script>
