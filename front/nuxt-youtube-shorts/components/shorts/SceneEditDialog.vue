<template>
	<div>
		<Dialog
			:visible="shortsStore.sceneEditDialogVisible"
			modal
			:center="true"
			:draggable="false"
			:style="{ width: '95vw', maxWidth: '800px', height: 'fit-content' }"
			:breakpoints="{ '960px': '90vw', '640px': '95vw' }"
			@update:visible="closeDialog"
		>
			<template #header>
				<div class="flex items-center h-full">
					<h3 class="font-semibold text-lg">씬 {{ state.selectedSceneIndex + 1 }} 수정</h3>
				</div>
			</template>

			<div v-if="state.targetSceneCopied">
				<div class="space-y-4 p-1">
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
							<div class="space-y-4">
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
												<Tag
													v-if="caption.animationEffect"
													:value="CaptionAnimationEffectInfo[caption.animationEffect].title"
													severity="info"
													size="small"
												/>
												<small v-if="caption.color" class="rounded-full" :style="{ color: caption.color }">자막</small>
											</div>
											<div class="flex items-center gap-2">
												<span class="text-xs text-slate-500">
													{{ caption.startTime.toFixed(1) }}s - {{ caption.endTime.toFixed(1) }}s
												</span>
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
										<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
											<!-- 텍스트 입력 -->
											<div class="field w-full">
												<label class="block mb-2 text-sm font-medium">텍스트</label>
												<div class="relative">
													<InputText
														v-model="caption.text"
														class="w-full"
														placeholder="자막 텍스트를 입력하세요 (최대 20자)"
														hide-details
														:maxlength="20"
													/>
													<small v-if="caption.text.length > 15" class="absolute right-1 bottom-1 text-orange-500 text-xs">
														{{ caption.text.length }}/20자
													</small>
												</div>
											</div>

											<!-- 시간 설정 -->
											<div class="field w-full">
												<label class="block mb-4 md:mb-6 text-sm font-medium">자막 시간 설정</label>
												<Slider
													v-model="state.timeRanges[index]"
													:min="0"
													:max="state.targetSceneCopied.duration"
													:step="0.1"
													range
													drag-range
													class="w-full"
													@slideend="handleTimeRangeUpdate(index)"
												/>
												<div class="flex justify-between text-xs text-slate-500 mt-1">
													<span>{{ state.timeRanges[index]?.[0]?.toFixed(1) }}초</span>
													<span>{{ state.timeRanges[index]?.[1]?.toFixed(1) }}초</span>
												</div>
											</div>

											<div class="field w-full">
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

											<div class="field w-full">
												<label class="block mb-2 text-sm font-medium">자막 색상</label>
												<div class="space-y-3">
													<!-- 잘 쓰이는 색상 팝오버 -->
													<div class="flex align-middle items-center gap-3">
														<Button
															:id="`color-button-${index}`"
															icon="pi pi-palette"
															size="small"
															severity="secondary"
															@click="(event: any) => openColorPopover(event, index)"
														/>

														<!-- 커스텀 색상 선택 -->
														<ColorPicker
															v-model="caption.color"
															:default-color="caption.color || '#ffffff'"
															format="hex"
															class="rounded border border-gray-300 shadow-sm"
															@update:model-value="(e) => (caption.color = '#' + e)"
														/>
														<InputText
															v-model="caption.color"
															v-tooltip="'색상을 직접 선택하거나 hex 코드를 입력하세요 (예: #ff0000)'"
															placeholder="#ffffff"
															class="w-full"
															:maxlength="7"
														/>
													</div>
												</div>
											</div>
										</div>
									</div>
								</div>

								<Button label="자막 추가" icon="pi pi-plus" class="w-full" severity="secondary" @click="addCaption" />
							</div>
						</AccordionTab>
					</Accordion>
				</div>
			</div>

			<template #footer>
				<div class="flex justify-end gap-2 h-full items-center">
					<Button label="취소" text @click="closeDialog" />
					<Button label="저장" @click="apply" />
				</div>
			</template>
		</Dialog>

		<!-- 공통 색상 팝오버 -->
		<Popover ref="colorPopover">
			<div class="p-3">
				<div class="text-sm font-medium mb-3">색상 선택</div>
				<div class="flex flex-wrap gap-2 max-w-48">
					<Button
						v-for="presetColor in presetColors"
						:key="presetColor.value"
						v-tooltip="presetColor.name"
						:style="{ backgroundColor: presetColor.value }"
						class="w-8 h-8 p-0 border-2 border-gray-300 rounded"
						:class="{ 'ring-2 ring-blue-500': getCurrentCaptionColor() === presetColor.value }"
						@click="selectPresetColor(presetColor.value)"
					>
						<span class="sr-only">{{ presetColor.name }}</span>
					</Button>
				</div>
			</div>
		</Popover>
	</div>
</template>

<script setup lang="ts">
	const shortsStore = useShortsStore();
	const { showMessage } = useMessageToast();
	const { showConfirm } = useConfirmDialog();

	const colorPopover = ref<{ toggle: (event: Event) => void; hide?: () => void } | null>(null);

	const state = reactive({
		timeRanges: [] as number[][],
		targetSceneCopied: {} as Scene,
		selectedSceneIndex: -1,
		allowCaptionCoincidence: false,
		currentCaptionIndex: -1
	});

	// 애니메이션 효과 옵션
	const animationEffectOptions = Object.entries(CaptionAnimationEffectInfo).map(([key, value]) => ({
		label: value.title,
		value: key
	}));

	// 프리셋 색상 옵션
	const presetColors = [
		{ name: '흰색', value: '#ffffff' },
		{ name: '검은색', value: '#000000' },
		{ name: '빨간색', value: '#ff0000' },
		{ name: '파란색', value: '#0066ff' },
		{ name: '초록색', value: '#00cc00' },
		{ name: '노란색', value: '#ffff00' },
		{ name: '주황색', value: '#ff6600' },
		{ name: '보라색', value: '#9933ff' },
		{ name: '분홍색', value: '#ff3399' },
		{ name: '청록색', value: '#00cccc' },
		{ name: '라임색', value: '#99ff00' },
		{ name: '마젠타', value: '#ff00ff' }
	];

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
		const maxDuration = state.targetSceneCopied.duration || 1;
		const minDuration = 0.2;

		// 최소 지속 시간 보장 (0.2초)
		let adjustedStart = start;
		let adjustedEnd = end;

		if (duration < minDuration) {
			if (start + minDuration <= maxDuration) {
				adjustedEnd = start + minDuration;
			} else {
				adjustedStart = Math.max(0, end - minDuration);
			}
		}

		// 시간 범위가 씬의 범위를 벗어나지 않도록 조정
		adjustedStart = Math.max(0, adjustedStart);
		adjustedEnd = Math.min(maxDuration, adjustedEnd);

		// 현재 자막의 조정된 시간 적용
		state.timeRanges[index] = [adjustedStart, adjustedEnd];
		caption.startTime = adjustedStart;
		caption.endTime = adjustedEnd;

		// 왼쪽(이전) 자막들과의 겹침 처리 및 밀어내기
		const pushCaptionsLeft = (startIndex: number): boolean => {
			let currentStart = state.timeRanges[startIndex][0];

			for (let i = startIndex - 1; i >= 0; i--) {
				const prevCaption = state.targetSceneCopied.captions[i];
				const [prevStart, prevEnd] = state.timeRanges[i];

				// 겹침이 있는 경우
				if (prevEnd > currentStart) {
					const newEnd = currentStart;
					const newStart = newEnd - (prevEnd - prevStart);

					// 새로운 시작 시간이 0보다 작은지 확인
					if (newStart < 0) {
						// 최소 시간을 보장할 수 있는지 확인
						const possibleStart = 0;
						const possibleEnd = possibleStart + minDuration;

						if (possibleEnd > currentStart) {
							// 최소 시간을 보장할 수 없으므로 false 반환
							return false;
						}

						state.timeRanges[i] = [possibleStart, possibleEnd];
						prevCaption.startTime = possibleStart;
						prevCaption.endTime = possibleEnd;
						currentStart = possibleStart;
					} else {
						// 최소 시간 보장 확인
						if (newEnd - newStart < minDuration) {
							const adjustedStart = newEnd - minDuration;
							if (adjustedStart < 0) {
								return false;
							}
							state.timeRanges[i] = [adjustedStart, newEnd];
							prevCaption.startTime = adjustedStart;
							prevCaption.endTime = newEnd;
							currentStart = adjustedStart;
						} else {
							state.timeRanges[i] = [newStart, newEnd];
							prevCaption.startTime = newStart;
							prevCaption.endTime = newEnd;
							currentStart = newStart;
						}
					}
				} else {
					// 겹침이 없으면 더 이상 처리할 필요 없음
					break;
				}
			}
			return true;
		};

		// 오른쪽(다음) 자막들과의 겹침 처리 및 밀어내기
		const pushCaptionsRight = (startIndex: number): boolean => {
			let currentEnd = state.timeRanges[startIndex][1];

			for (let i = startIndex + 1; i < state.targetSceneCopied.captions.length; i++) {
				const nextCaption = state.targetSceneCopied.captions[i];
				const [nextStart, nextEnd] = state.timeRanges[i];

				// 겹침이 있는 경우
				if (nextStart < currentEnd) {
					const newStart = currentEnd;
					const newEnd = newStart + (nextEnd - nextStart);

					// 새로운 끝 시간이 씬의 최대 시간을 초과하는지 확인
					if (newEnd > maxDuration) {
						// 최소 시간을 보장할 수 있는지 확인
						const possibleEnd = maxDuration;
						const possibleStart = possibleEnd - minDuration;

						if (possibleStart < currentEnd) {
							// 최소 시간을 보장할 수 없으므로 false 반환
							return false;
						}

						state.timeRanges[i] = [possibleStart, possibleEnd];
						nextCaption.startTime = possibleStart;
						nextCaption.endTime = possibleEnd;
						currentEnd = possibleEnd;
					} else {
						// 최소 시간 보장 확인
						if (newEnd - newStart < minDuration) {
							const adjustedEnd = newStart + minDuration;
							if (adjustedEnd > maxDuration) {
								return false;
							}
							state.timeRanges[i] = [newStart, adjustedEnd];
							nextCaption.startTime = newStart;
							nextCaption.endTime = adjustedEnd;
							currentEnd = adjustedEnd;
						} else {
							state.timeRanges[i] = [newStart, newEnd];
							nextCaption.startTime = newStart;
							nextCaption.endTime = newEnd;
							currentEnd = newEnd;
						}
					}
				} else {
					// 겹침이 없으면 더 이상 처리할 필요 없음
					break;
				}
			}
			return true;
		};

		// 양방향 처리를 위한 전체 조정 함수
		const adjustAllCaptions = (): boolean => {
			// 먼저 왼쪽 밀어내기 시도
			if (!pushCaptionsLeft(index)) {
				return false;
			}

			// 그 다음 오른쪽 밀어내기 시도
			if (!pushCaptionsRight(index)) {
				return false;
			}

			return true;
		};

		// 전체 조정 시도
		if (!adjustAllCaptions()) {
			// 조정 실패 시 롤백 메커니즘
			let rollbackIndex = index;
			let success = false;

			while (rollbackIndex >= 0 && !success) {
				// 원본 상태 백업
				const originalRanges = [...state.timeRanges];
				const originalCaptions = state.targetSceneCopied.captions.map((c) => ({ ...c }));

				// rollbackIndex 자막을 약간 조정하여 공간 확보 시도
				if (rollbackIndex > 0) {
					const prevEnd = rollbackIndex > 0 ? state.timeRanges[rollbackIndex - 1][1] : 0;
					const nextStart = rollbackIndex < state.targetSceneCopied.captions.length - 1 ? state.timeRanges[rollbackIndex + 1][0] : maxDuration;

					const currentDuration = state.timeRanges[rollbackIndex][1] - state.timeRanges[rollbackIndex][0];
					const availableSpace = nextStart - prevEnd;

					if (availableSpace >= currentDuration + 0.1) {
						// 약간의 여유 공간이 있으면 자막을 중앙에 배치
						const newStart = prevEnd + (availableSpace - currentDuration) / 2;
						const newEnd = newStart + currentDuration;

						state.timeRanges[rollbackIndex] = [newStart, newEnd];
						state.targetSceneCopied.captions[rollbackIndex].startTime = newStart;
						state.targetSceneCopied.captions[rollbackIndex].endTime = newEnd;

						// 전체 조정 다시 시도
						if (adjustAllCaptions()) {
							success = true;
							break;
						}
					}
				}

				if (!success) {
					// 복원
					state.timeRanges = originalRanges;
					for (let i = 0; i < state.targetSceneCopied.captions.length; i++) {
						state.targetSceneCopied.captions[i].startTime = originalCaptions[i].startTime;
						state.targetSceneCopied.captions[i].endTime = originalCaptions[i].endTime;
					}
				}

				rollbackIndex--;
			}

			// 역방향 롤백도 시도
			if (!success) {
				rollbackIndex = index + 1;

				while (rollbackIndex < state.targetSceneCopied.captions.length && !success) {
					const originalRanges = [...state.timeRanges];
					const originalCaptions = state.targetSceneCopied.captions.map((c) => ({ ...c }));

					const prevEnd = rollbackIndex > 0 ? state.timeRanges[rollbackIndex - 1][1] : 0;
					const nextStart = rollbackIndex < state.targetSceneCopied.captions.length - 1 ? state.timeRanges[rollbackIndex + 1][0] : maxDuration;

					const currentDuration = state.timeRanges[rollbackIndex][1] - state.timeRanges[rollbackIndex][0];
					const availableSpace = nextStart - prevEnd;

					if (availableSpace >= currentDuration + 0.1) {
						const newStart = prevEnd + (availableSpace - currentDuration) / 2;
						const newEnd = newStart + currentDuration;

						state.timeRanges[rollbackIndex] = [newStart, newEnd];
						state.targetSceneCopied.captions[rollbackIndex].startTime = newStart;
						state.targetSceneCopied.captions[rollbackIndex].endTime = newEnd;

						if (adjustAllCaptions()) {
							success = true;
							break;
						}
					}

					if (!success) {
						// 복원
						state.timeRanges = originalRanges;
						for (let i = 0; i < state.targetSceneCopied.captions.length; i++) {
							state.targetSceneCopied.captions[i].startTime = originalCaptions[i].startTime;
							state.targetSceneCopied.captions[i].endTime = originalCaptions[i].endTime;
						}
					}

					rollbackIndex++;
				}
			}
		}
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
			animationEffect: undefined
		});
		state.timeRanges.push([startTime, endTime]);
	};

	// 자막 삭제
	const deleteCaption = (index: number) => {
		state.targetSceneCopied.captions.splice(index, 1);
		state.timeRanges.splice(index, 1);
	};

	// 색상 팝오버 열기
	const openColorPopover = (event: Event, index: number) => {
		state.currentCaptionIndex = index;
		if (colorPopover.value) {
			colorPopover.value.toggle(event);
		}
	};

	// 현재 자막의 색상 가져오기
	const getCurrentCaptionColor = () => {
		if (state.currentCaptionIndex >= 0 && state.targetSceneCopied.captions[state.currentCaptionIndex]) {
			return state.targetSceneCopied.captions[state.currentCaptionIndex].color;
		}
		return '#ffffff';
	};

	// 프리셋 색상 선택
	const selectPresetColor = (color: string) => {
		if (state.currentCaptionIndex >= 0 && state.targetSceneCopied.captions[state.currentCaptionIndex]) {
			state.targetSceneCopied.captions[state.currentCaptionIndex].color = color;
		}
		// 팝오버 닫기
		if (colorPopover.value) {
			colorPopover.value.hide?.();
		}
	};

	const apply = async () => {
		state.targetSceneCopied.captions.forEach((caption) => {
			if (caption.color && !caption.color.startsWith('#')) {
				caption.color = '#' + caption.color;
			}
		});

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
