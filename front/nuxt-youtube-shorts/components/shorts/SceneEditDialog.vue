<template>
	<div>
		<Dialog :visible="shortsStore.sceneEditDialogVisible" :header="'씬 ' + (state.selectedSceneIndex + 1) + ' 수정'" modal @update:visible="closeDialog">
			<div v-if="state.targetSceneCopied" class="space-y-4 min-w-[350px] max-h-[600px]">
				<Accordion>
					<AccordionTab header="씬 정보">
						<div class="space-y-4">
							<div class="field">
								<label class="block mb-2">설명</label>
								<InputText v-model="state.targetSceneCopied.description" class="w-full" placeholder="씬에 대한 설명을 입력하세요" />
							</div>
							<div class="field">
								<label class="block mb-2">지속 시간 (초)</label>
								<InputNumber
									v-model="state.targetSceneCopied.duration"
									:min="0.1"
									:max="10"
									:step="0.1"
									class="w-full"
									:min-fraction-digits="1"
								/>
							</div>
						</div>
					</AccordionTab>
				</Accordion>

				<Accordion>
					<AccordionTab header="자막">
						<template #header></template>
						<div class="space-y-4 max-h-[400px] custom-scroll pr-2">
							<div v-if="state.targetSceneCopied.captions.length === 0" class="text-center py-4 text-slate-500">
								자막이 없습니다. 자막을 추가해주세요.
							</div>
							<div v-for="(caption, index) in state.targetSceneCopied.captions" :key="index" class="p-4 bg-surface-50 rounded-lg">
								<Accordion>
									<AccordionTab>
										<template #header>
											<div class="flex items-center justify-between w-full">
												<div class="flex items-center gap-2">
													<span class="font-medium">자막 {{ index + 1 }}</span>
													<Tag :value="`${(caption.endTime - caption.startTime).toFixed(1)}초`" severity="info" />
												</div>
												<div class="flex items-center gap-2">
													<span class="text-sm text-slate-500">
														{{ caption.startTime.toFixed(1) }}초 - {{ caption.endTime.toFixed(1) }}초
													</span>
													<Button v-tooltip="'자막 삭제'" icon="pi pi-trash" text severity="danger" @click="deleteCaption(index)" />
												</div>
											</div>
										</template>
										<div class="space-y-4">
											<div class="field">
												<label class="block mb-2">텍스트</label>
												<InputText
													v-model="caption.text"
													class="w-full"
													placeholder="자막 텍스트를 입력하세요 (최대 20자)"
													:maxlength="20"
												/>
												<small v-if="caption.text.length > 20" class="text-red-500">자막은 최대 20자까지 입력 가능합니다.</small>
											</div>
											<div class="field">
												<label class="block mb-2">자막 시간 설정</label>
												<div class="flex items-center gap-2">
													<Slider
														v-model="state.timeRanges[index]"
														:min="0"
														:max="state.targetSceneCopied.duration"
														:step="0.1"
														range
														drag-range
														class="w-full"
														@update:model-value="handleTimeRangeUpdate(index)"
													/>
												</div>
											</div>
										</div>
									</AccordionTab>
								</Accordion>
							</div>
							<Button label="자막 추가" icon="pi pi-plus" class="w-full p-4" @click="addCaption" />
						</div>
					</AccordionTab>
				</Accordion>
			</div>
			<template #footer>
				<Button label="취소" text @click="closeDialog" />
				<Button label="저장" @click="apply" />
			</template>
		</Dialog>
	</div>
</template>

<script setup lang="ts">
	const shortsStore = useShortsStore();
	const { showMessage } = useMessageToast();
	const { showConfirm } = useConfirmDialog();
	const state = reactive({
		timeRanges: [] as number[][],
		targetSceneCopied: {} as Scene,
		selectedSceneIndex: -1
	});

	watch(
		() => shortsStore.sceneEditDialogVisible,
		(visible) => {
			if (visible) {
				state.selectedSceneIndex = shortsStore.targetSceneIndex;
				state.targetSceneCopied = JSON.parse(JSON.stringify(shortsStore.script?.scenes[state.selectedSceneIndex] as Scene));
				if (state.targetSceneCopied) {
					state.targetSceneCopied.captions.forEach((caption) => {
						state.timeRanges.push([caption.startTime, caption.endTime]);
					});
				}
			}
		}
	);

	const handleTimeRangeUpdate = (index: number) => {
		const caption = state.targetSceneCopied.captions[index];
		if (!caption) return;

		const [start, end] = state.timeRanges[index];
		const duration = end - start;

		// 최소 지속 시간 보장 (0.2초)
		if (duration < 0.2) {
			if (start + 0.2 <= state.targetSceneCopied.duration) {
				state.timeRanges[index] = [start, start + 0.2];
			} else {
				state.timeRanges[index] = [Math.max(0, end - 0.2), end];
			}
		}

		// 자막 시간 범위 업데이트
		caption.startTime = state.timeRanges[index][0];
		caption.endTime = state.timeRanges[index][1];
	};

	const closeDialog = () => {
		shortsStore.setSceneEditDialogVisible(false);
		shortsStore.setTargetSceneIndex(-1);
		state.timeRanges = [];
		state.targetSceneCopied = {} as Scene;
	};

	// 자막 추가
	const addCaption = () => {
		const lastCaption = state.targetSceneCopied.captions[state.targetSceneCopied.captions.length - 1];
		const startTime = lastCaption ? lastCaption.endTime : 0;
		const endTime = Math.min(startTime + 0.2, state.targetSceneCopied.duration || 0);

		if (endTime - startTime < 0.2) {
			showMessage('적어도 0.2초의 남은 시간이 있어야 합니다', 'error');
			return;
		}

		state.targetSceneCopied.captions.push({
			text: '',
			startTime: startTime,
			endTime: endTime
		});
		state.timeRanges.push([startTime, endTime]);
	};

	// 자막 삭제
	const deleteCaption = (index: number) => {
		state.targetSceneCopied.captions.splice(index, 1);
		state.timeRanges.splice(index, 1);
	};

	const apply = async () => {
		// 자막 시간 범위가 겹치는지 확인
		const hasOverlappingTimeRanges = state.timeRanges.some((range1, index1) => {
			return state.timeRanges.some((range2, index2) => {
				if (index1 === index2) return false;
				const [start1, end1] = range1;
				const [start2, end2] = range2;
				return start1 < end2 && end1 > start2;
			});
		});

		if (hasOverlappingTimeRanges) {
			if (await showConfirm({ message: '자막 시간이 겹치는 부분이 있습니다. 계속 진행하시겠습니까?', header: '경고' })) {
				shortsStore.script!.scenes[state.selectedSceneIndex] = state.targetSceneCopied;
				closeDialog();
			}
		} else {
			shortsStore.script!.scenes[state.selectedSceneIndex] = state.targetSceneCopied;
			closeDialog();
		}
	};
</script>
