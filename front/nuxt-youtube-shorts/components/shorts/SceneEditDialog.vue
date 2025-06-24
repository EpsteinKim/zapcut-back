<template>
	<div>
		<Dialog
			:visible="shortsStore.sceneEditDialogVisible"
			:header="'씬 ' + (state.selectedSceneIndex + 1) + ' 수정'"
			modal
			:style="{ width: '95vw', maxWidth: '800px' }"
			:breakpoints="{ '960px': '90vw', '640px': '95vw' }"
			@update:visible="closeDialog"
		>
			<div v-if="state.targetSceneCopied" class="space-y-4">
				<Accordion>
					<AccordionTab header="씬 정보">
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div class="field">
								<label class="block mb-2 text-sm font-medium">설명</label>
								<InputText v-model="state.targetSceneCopied.description" class="w-full" placeholder="씬에 대한 설명을 입력하세요" />
							</div>
							<div class="field">
								<label class="block mb-2 text-sm font-medium">지속 시간 (초)</label>
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
					<AccordionTab header="자막 설정">
						<div class="space-y-4 max-h-[500px] overflow-y-auto custom-scroll pr-2">
							<div v-if="state.targetSceneCopied.captions.length === 0" class="text-center py-8 text-slate-500">
								<i class="pi pi-comment text-4xl mb-2 block"></i>
								<p>자막이 없습니다. 자막을 추가해주세요.</p>
							</div>

							<div
								v-for="(caption, index) in state.targetSceneCopied.captions"
								:key="index"
								class="border border-surface-200 rounded-lg overflow-hidden"
							>
								<div class="bg-surface-50 p-3 border-b border-surface-200">
									<div class="flex items-center justify-between">
										<div class="flex items-center gap-2">
											<span class="font-medium text-sm">자막 {{ index + 1 }}</span>
											<Tag :value="`${(caption.endTime - caption.startTime).toFixed(1)}초`" severity="info" size="small" />
										</div>
										<div class="flex items-center gap-2">
											<span class="text-xs text-slate-500">{{ caption.startTime.toFixed(1) }}s - {{ caption.endTime.toFixed(1) }}s</span>
											<Button
												v-tooltip="'자막 삭제'"
												icon="pi pi-trash"
												text
												severity="danger"
												size="small"
												@click="deleteCaption(index)"
											/>
										</div>
									</div>
								</div>

								<div class="p-4 space-y-4">
									<!-- 텍스트 입력 -->
									<div class="field">
										<label class="block mb-2 text-sm font-medium">텍스트</label>
										<InputText v-model="caption.text" class="w-full" placeholder="자막 텍스트를 입력하세요 (최대 20자)" :maxlength="20" />
										<small v-if="caption.text.length > 15" class="text-orange-500">{{ caption.text.length }}/20자</small>
									</div>

									<!-- 시간 설정 -->
									<div class="field">
										<label class="block mb-2 text-sm font-medium">자막 시간 설정</label>
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
										<div class="flex justify-between text-xs text-slate-500 mt-1">
											<span>{{ state.timeRanges[index]?.[0]?.toFixed(1) }}초</span>
											<span>{{ state.timeRanges[index]?.[1]?.toFixed(1) }}초</span>
										</div>
									</div>

									<!-- 애니메이션 효과 -->
									<div class="flex flex-col sm:flex-row gap-2">
										<div class="field flex-1">
											<label class="block mb-2 text-sm font-medium">애니메이션 효과</label>
											<Select
												v-model="caption.animationEffect"
												:options="animationEffectOptions"
												filter
												show-clear
												option-label="label"
												option-value="value"
												placeholder="애니메이션 효과 선택"
												class="w-full"
												:clearable="true"
											/>
										</div>

										<!-- 스타일 효과 -->
										<div class="field flex-1">
											<label class="block mb-2 text-sm font-medium" @click="console.log(caption)">스타일 효과</label>
											<MultiSelect
												v-model="caption.styleEffects"
												:options="styleEffectOptions"
												option-label="label"
												option-value="value"
												placeholder="스타일 효과 선택 (다중 선택 가능)"
												:show-toggle-all="false"
												filter
												class="w-full"
												:max-selected-labels="3"
											/>
										</div>
									</div>

									<!-- 효과 미리보기 -->
									<div
										v-if="caption.animationEffect || (caption.styleEffects && caption.styleEffects.length > 0)"
										class="bg-slate-50 p-3 rounded-lg"
									>
										<div class="text-xs text-slate-600 mb-2">적용된 효과:</div>
										<div class="flex flex-wrap gap-1">
											<Tag
												v-if="caption.animationEffect"
												:value="CaptionAnimationEffectInfo[caption.animationEffect].title"
												severity="info"
												size="small"
											/>
											<Tag
												v-for="effect in caption.styleEffects"
												:key="effect"
												:value="StyleEffectInfo[effect].title"
												severity="success"
												size="small"
											/>
										</div>
									</div>
								</div>
							</div>

							<Button label="자막 추가" icon="pi pi-plus" class="w-full" severity="secondary" @click="addCaption" />
						</div>
					</AccordionTab>
				</Accordion>
			</div>
			<template #footer>
				<div class="flex justify-end gap-2">
					<Button label="취소" text @click="closeDialog" />
					<Button label="저장" @click="apply" />
				</div>
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
		selectedSceneIndex: -1,
		allowCaptionCoincidence: false
	});

	// 애니메이션 효과 옵션
	const animationEffectOptions = Object.entries(CaptionAnimationEffectInfo).map(([key, value]) => ({
		label: value.title,
		value: key
	}));
	// 스타일 효과 옵션
	const styleEffectOptions = Object.entries(StyleEffectInfo).map(([key, value]) => ({
		label: value.title,
		value: key
	}));

	watch(
		() => shortsStore.sceneEditDialogVisible,
		(visible) => {
			if (visible) {
				state.selectedSceneIndex = shortsStore.targetSceneIndex;
				state.targetSceneCopied = JSON.parse(JSON.stringify(shortsStore.script?.scenes[state.selectedSceneIndex] as Scene));
				if (state.targetSceneCopied) {
					// 자막 시간 범위 초기화
					state.timeRanges = [];
					state.targetSceneCopied.captions.forEach((caption) => {
						state.timeRanges.push([caption.startTime, caption.endTime]);
						// 기본값 설정
						if (!caption.animationEffect) {
							caption.animationEffect = undefined;
						}
						if (!caption.styleEffects) {
							caption.styleEffects = [];
						}
					});
				}
			} else {
				// 다이얼로그가 닫힐 때 상태 초기화
				state.timeRanges = [];
				state.targetSceneCopied = {} as Scene;
				state.selectedSceneIndex = -1;
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
	};

	// 자막 추가
	const addCaption = () => {
		const lastCaption = state.targetSceneCopied.captions[state.targetSceneCopied.captions.length - 1];
		const startTime = lastCaption ? lastCaption.endTime : 0;
		const endTime = Math.min(startTime + 1, state.targetSceneCopied.duration || 1);

		if (endTime - startTime < 0.2) {
			showMessage('적어도 0.2초의 남은 시간이 있어야 합니다', 'error');
			return;
		}

		state.targetSceneCopied.captions.push({
			text: '',
			startTime: startTime,
			endTime: endTime,
			animationEffect: undefined,
			styleEffects: []
		});
		state.timeRanges.push([startTime, endTime]);
	};

	// 자막 삭제
	const deleteCaption = (index: number) => {
		state.targetSceneCopied.captions.splice(index, 1);
		state.timeRanges.splice(index, 1);
	};

	const apply = async () => {
		// 빈 텍스트 자막 확인
		const emptyTextCaptions = state.targetSceneCopied.captions.filter((caption) => !caption.text.trim());
		if (emptyTextCaptions.length > 0) {
			showMessage('빈 텍스트가 있는 자막이 있습니다. 텍스트를 입력하거나 자막을 삭제해주세요.', 'error');
			return;
		}

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
				showMessage('씬이 성공적으로 저장되었습니다', 'success');
			}
		} else {
			shortsStore.script!.scenes[state.selectedSceneIndex] = state.targetSceneCopied;
			closeDialog();
			showMessage('씬이 성공적으로 저장되었습니다', 'success');
		}
	};
</script>

<style scoped>
	.custom-scroll {
		scrollbar-width: thin;
		scrollbar-color: #cbd5e1 transparent;
	}

	.custom-scroll::-webkit-scrollbar {
		width: 6px;
	}

	.custom-scroll::-webkit-scrollbar-track {
		background: transparent;
	}

	.custom-scroll::-webkit-scrollbar-thumb {
		background-color: #cbd5e1;
		border-radius: 3px;
	}

	.custom-scroll::-webkit-scrollbar-thumb:hover {
		background-color: #94a3b8;
	}
</style>
