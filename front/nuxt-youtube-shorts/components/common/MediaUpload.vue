<template>
	<div>
		<div @click="openDialog" @dragover.prevent @dragenter.prevent @drop.prevent.stop="onDropFile" @hide="closeDialog">
			<slot />
		</div>
		<Dialog v-if="props.allowDialog" v-model:visible="state.isDialogVisible" modal header="미디어 등록/수정" :style="{ width: '900px' }">
			<div class="max-w-[900px] mx-auto rounded-2xl pb-4">
				<div class="flex justify-center items-center">
					<div
						v-if="state.uploadedUrl"
						class="max-w-[600px] max-h-[600px] rounded-xl flex flex-col items-center justify-center overflow-hidden relative"
					>
						<div v-if="mediaType === 'video'">
							<video
								ref="mediaRef"
								:src="state.uploadedUrl"
								controls
								class="max-w-full max-h-[480px] rounded-lg bg-white"
								@loadedmetadata="updateMediaSize"
							/>
						</div>
						<div v-else-if="mediaType === 'image'">
							<img ref="mediaRef" :src="state.uploadedUrl" class="max-w-full max-h-[480px] rounded-lg bg-white" @load="updateMediaSize" />
						</div>
						<div v-else-if="mediaType === 'audio'" class="flex w-[600px] flex-col items-center justify-center h-full">
							<audio ref="mediaRef" :src="state.uploadedUrl" controls class="w-full" @loadedmetadata="updateMediaSize" />
							<span class="text-gray-500 mt-2">오디오 미리듣기</span>
						</div>
						<div v-if="mediaWidth && mediaHeight" class="text-center mt-2">사이즈 : {{ mediaWidth }}x{{ mediaHeight }}</div>
					</div>
					<div
						v-else
						class="min-w-[480px] min-h-[480px] max-w-[600px] max-h-[600px] bg-[#fafbfc] border border-gray-200 rounded-xl flex items-center justify-center text-gray-400"
					>
						미리보기 없음
					</div>
				</div>
				<div class="mt-4">
					<label class="block text-sm font-medium mb-1">미디어 URL</label>
					<div class="flex gap-2">
						<InputText v-model="state.uploadedUrl" readonly class="flex-1" />
						<Button icon="pi pi-copy" @click="copyUrl" />
					</div>
				</div>
				<div class="mt-4">
					<FileUpload
						mode="basic"
						custom-upload
						auto
						:multiple="props.allowMultiple"
						:accept="getAcceptString"
						:max-file-size="props.maxFileSize * 1024 * 1024"
						choose-label="파일 업로드"
						class="w-full"
						:pt="{ filename: 'hidden' }"
						@select="handleUpload"
					/>
					<div
						class="border-2 border-dashed border-slate-300 rounded-lg p-4 text-center text-slate-500 bg-slate-50 text-[15px] mt-2 cursor-pointer"
						@dragover.prevent
						@dragenter.prevent
						@drop.prevent.stop="onDropFile"
					>
						이미지를 클릭하거나,
						<span class="font-semibold">이곳에 드래그 & 드롭</span>
						하여 파일{{ props.allowMultiple ? '들' : '' }}을 업로드 할 수 있습니다.
					</div>
				</div>
				<div v-if="state.isUploading" class="w-full mt-2">
					<div class="w-full bg-gray-200 rounded-full h-2.5">
						<div class="bg-blue-500 h-2.5 rounded-full" :style="{ width: state.uploadPercent + '%' }"></div>
					</div>
					<div class="text-right text-xs text-gray-500 mt-1">{{ state.uploadPercent }}%</div>
				</div>
			</div>
			<template #footer>
				<div class="flex justify-end gap-2 w-full">
					<Button label="취소" severity="secondary" @click="closeDialog" />
					<Button label="적용(↵)" @click="applyMedia" />
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup lang="ts">
	import type { FileUploadSelectEvent } from 'primevue/fileupload';

	const props = withDefaults(
		defineProps<{
			allowDialog?: boolean;
			src?: string;
			userId?: string;
			allowedTypes?: ('video' | 'image' | 'audio')[];
			maxFileSize?: number;
			allowMultiple?: boolean;
		}>(),
		{
			allowDialog: true,
			userId: '1',
			allowedTypes: () => ['video', 'image', 'audio'],
			maxFileSize: 30, // mb
			allowMultiple: false
		}
	);

	const emit = defineEmits<{
		(e: 'upload-complete', url: string): void;
		(e: 'upload-progress', percent: number): void;
		(e: 'upload-state-change', state: 'start' | 'end'): void;
	}>();

	const toast = useToast();
	const { showMessage } = useMessageToast();

	const state = reactive({
		isUploading: false,
		isDialogVisible: false,
		uploadedUrl: null as string | null,
		mediaMime: '' as string,
		uploadPercent: 0
	});

	const openDialog = () => {
		state.isDialogVisible = true;
		state.uploadedUrl = props.src || null;
	};

	const getMediaType = (url: string, mime: string) => {
		if (mime.startsWith('video/')) return 'video';
		if (mime.startsWith('audio/')) return 'audio';
		if (mime.startsWith('image/')) return 'image';
		if (url.match(/\.(mp4|webm|ogg)$/i)) return 'video';
		if (url.match(/\.(mp3|wav|aac|m4a)$/i)) return 'audio';
		if (url.match(/\.(jpg|jpeg|png|gif|webp)$/i)) return 'image';
		return '';
	};

	const mediaType = computed(() => {
		return getMediaType(state.uploadedUrl || '', state.mediaMime);
	});

	const mediaRef = ref<HTMLVideoElement | HTMLImageElement | HTMLAudioElement | null>(null);
	const mediaWidth = ref<number | null>(null);
	const mediaHeight = ref<number | null>(null);

	const updateMediaSize = () => {
		if (!mediaRef.value) return;
		if (mediaType.value === 'image') {
			mediaWidth.value = (mediaRef.value as HTMLImageElement).naturalWidth;
			mediaHeight.value = (mediaRef.value as HTMLImageElement).naturalHeight;
		} else if (mediaType.value === 'video') {
			mediaWidth.value = (mediaRef.value as HTMLVideoElement).videoWidth;
			mediaHeight.value = (mediaRef.value as HTMLVideoElement).videoHeight;
		} else {
			mediaWidth.value = null;
			mediaHeight.value = null;
		}
	};

	onMounted(() => {
		if (props.src) {
			state.uploadedUrl = props.src;
			state.mediaMime = '';
		}
	});

	watch(
		() => state.uploadedUrl,
		(url) => {
			if (!url) {
				mediaWidth.value = null;
				mediaHeight.value = null;
				return;
			}
			if (!state.mediaMime && url) {
				state.mediaMime = '';
			}
		}
	);

	// 단일 파일 처리 함수
	const handleSingleFile = async (file: File) => {
		if (!file) return;

		if (file.size > props.maxFileSize * 1024 * 1024) {
			showMessage(`파일 크기는 ${props.maxFileSize}MB를 초과할 수 없습니다.`, 'error');
			return;
		}

		const fileType = getMediaType(file.name, file.type);
		if (!fileType || !props.allowedTypes.includes(fileType)) {
			showMessage(`${props.allowedTypes.join(', ')} 파일만 업로드 가능합니다.`, 'error');
			return;
		}

		if (fileType === 'video') {
			const isValidDuration = await checkVideoDuration(file);
			if (!isValidDuration) return;
		}

		state.uploadPercent = 0;
		try {
			state.isUploading = true;
			emit('upload-state-change', 'start');
			const fileUrl = await uploadToS3(file, props.userId, (percent) => {
				state.uploadPercent = percent;
				emit('upload-progress', percent);
			});
			state.uploadedUrl = fileUrl;
			state.mediaMime = file.type;
			showMessage('파일이 업로드되었습니다', 'success');
			emit('upload-complete', fileUrl);
		} catch (e) {
			showMessage('파일 업로드에 실패했습니다: ' + (e instanceof Error ? e.message : String(e)), 'error');
		} finally {
			state.isUploading = false;
			state.uploadPercent = 0;
			emit('upload-state-change', 'end');
		}
	};

	const handleUpload = async (event: FileUploadSelectEvent) => {
		if (props.allowMultiple) {
			// 다중 업로드 허용 시 모든 파일을 순차적으로 업로드
			for (let i = 0; i < event.files.length; i++) {
				const file = event.files[i];
				await handleSingleFile(file);
			}
		} else {
			// 단일 업로드만 허용 시 첫 번째 파일만 업로드
			const file = event.files[0];
			await handleSingleFile(file);
		}
	};

	const closeDialog = () => {
		state.isDialogVisible = false;
		state.uploadedUrl = null;
		mediaWidth.value = null;
		mediaHeight.value = null;
	};

	const copyUrl = () => {
		if (!state.uploadedUrl) return;
		navigator.clipboard.writeText(state.uploadedUrl);
		toast.add({ severity: 'success', summary: 'URL이 복사되었습니다', life: 3000 });
	};

	const applyMedia = () => {
		if (state.uploadedUrl) {
			emit('upload-complete', state.uploadedUrl);
			state.isDialogVisible = false;
		}
	};

	const checkVideoDuration = (file: File): Promise<boolean> => {
		return new Promise((resolve) => {
			const video = document.createElement('video');
			video.preload = 'metadata';
			video.onloadedmetadata = () => {
				URL.revokeObjectURL(video.src);
				if (video.duration > 60) {
					showMessage('비디오 길이는 30초를 초과할 수 없습니다.', 'error');
					resolve(false);
				} else {
					resolve(true);
				}
			};
			video.onerror = () => {
				URL.revokeObjectURL(video.src);
				showMessage('비디오 파일을 확인할 수 없습니다.', 'error');
				resolve(false);
			};
			video.src = URL.createObjectURL(file);
		});
	};

	// 드래그&드롭 파일 업로드 핸들러
	const onDropFile = async (event: DragEvent) => {
		const files = event.dataTransfer?.files;
		if (files && files.length > 0) {
			if (props.allowMultiple) {
				// 다중 업로드 허용 시 모든 파일을 순차적으로 업로드
				for (let i = 0; i < files.length; i++) {
					const file = files[i];
					await handleSingleFile(file);
				}
			} else {
				// 단일 업로드만 허용 시 첫 번째 파일만 업로드
				await handleSingleFile(files[0]);
			}
		}
	};

	const getAcceptString = computed(() => {
		const acceptMap = {
			video: 'video/*',
			image: 'image/*',
			audio: 'audio/*'
		};
		return props.allowedTypes.map((type) => acceptMap[type]).join(',');
	});
</script>
