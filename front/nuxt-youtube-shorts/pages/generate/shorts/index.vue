<template>
	<ScriptGenerator v-if="!shortsStore.script" />
	<VideoEditor v-else />
</template>

<script setup lang="ts">
	const shortsStore = useShortsStore();

	onMounted(() => {
		// shortsStore.setVideoUrl('https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_299234676562700751749732816203.mp4');
		// shortsStore.setScript({
		// 	title: '앙뜨레 캐리어 리뷰: 가성비 끝판왕?',
		// 	scenes: [
		// 		{
		// 			duration: 2,
		// 			captions: [
		// 				{
		// 					text: '여행 필수템!',
		// 					startTime: 0.3,
		// 					endTime: 1.7
		// 				}
		// 			],
		// 			description: '다양한 색상의 캐리어들이 회전하며 등장하는 모습. 활기찬 배경 음악.',
		// 			voiceUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_212430461004903931750230154941.mp3',
		// 			videoUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_80070166706570191750230142591.mp4'
		// 		},
		// 		{
		// 			duration: 3,
		// 			captions: [
		// 				{
		// 					text: '가성비 캐리어 찾고 있다면?',
		// 					startTime: 0.1,
		// 					endTime: 1
		// 				},
		// 				{
		// 					text: '앙뜨레 캐리어 주목!',
		// 					startTime: 1,
		// 					endTime: 2.8
		// 				}
		// 			],
		// 			description: '앙뜨레 캐리어를 들고 공항을 활보하는 모습. 세련된 여행자 스타일.',
		// 			voiceUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_0227148143239006561750230159583.mp3',
		// 			imageUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_290298094569553241750230143015.jpg'
		// 		},
		// 		{
		// 			duration: 4,
		// 			captions: [
		// 				{
		// 					text: '견고함은 기본!',
		// 					startTime: 0.2,
		// 					endTime: 1
		// 				},
		// 				{
		// 					text: 'PC소재로 튼튼하게!',
		// 					startTime: 1,
		// 					endTime: 2
		// 				},
		// 				{
		// 					text: '스크래치 걱정 No!',
		// 					startTime: 2,
		// 					endTime: 3.7
		// 				}
		// 			],
		// 			description: '캐리어 표면을 클로즈업하여 PC 소재의 질감을 보여준다. 망치로 살짝 두드리는 시늉.',
		// 			voiceUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_018686201179571871750230165563.mp3',
		// 			imageUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_45646929109598221750230143277.jpg'
		// 		},
		// 		{
		// 			duration: 3,
		// 			captions: [
		// 				{
		// 					text: '부드러운 주행감!',
		// 					startTime: 0.1,
		// 					endTime: 1
		// 				},
		// 				{
		// 					text: '360도 더블 휠!',
		// 					startTime: 1,
		// 					endTime: 2.8
		// 				}
		// 			],
		// 			description: '캐리어 바퀴가 부드럽게 회전하는 모습. 다양한 방향으로 움직이는 것을 보여준다.',
		// 			voiceUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_28804782435643371750230169464.mp3',
		// 			imageUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_62455482846620321750230143546.jpg'
		// 		},
		// 		{
		// 			duration: 4,
		// 			captions: [
		// 				{
		// 					text: '넉넉한 수납공간!',
		// 					startTime: 0.2,
		// 					endTime: 1
		// 				},
		// 				{
		// 					text: '짐 정리 걱정 끝!',
		// 					startTime: 1,
		// 					endTime: 2
		// 				},
		// 				{
		// 					text: 'X자형 밴드와 메시 포켓!',
		// 					startTime: 2,
		// 					endTime: 3.7
		// 				}
		// 			],
		// 			description: '캐리어 내부를 보여주며 짐을 효율적으로 수납하는 모습. X자 밴드와 메시 포켓 강조.',
		// 			voiceUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_72345470835247541750230174802.mp3'
		// 		},
		// 		{
		// 			duration: 3,
		// 			captions: [
		// 				{
		// 					text: '안전한 TSA 잠금!',
		// 					startTime: 0.1,
		// 					endTime: 1
		// 				},
		// 				{
		// 					text: '도난 걱정 없이!',
		// 					startTime: 1,
		// 					endTime: 2.8
		// 				}
		// 			],
		// 			description: 'TSA 잠금장치를 클로즈업하여 보여준다. 비밀번호 설정하는 모습.',
		// 			voiceUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_404090117655586441750230179936.mp3'
		// 		},
		// 		{
		// 			duration: 4,
		// 			captions: [
		// 				{
		// 					text: '나에게 맞는 사이즈는?',
		// 					startTime: 0.2,
		// 					endTime: 1
		// 				},
		// 				{
		// 					text: '기내용부터 화물용까지!',
		// 					startTime: 1,
		// 					endTime: 2
		// 				},
		// 				{
		// 					text: '다양한 사이즈!',
		// 					startTime: 2,
		// 					endTime: 3.7
		// 				}
		// 			],
		// 			description: '다양한 크기의 앙뜨레 캐리어를 나란히 보여준다. 크기 비교 가능하도록.',
		// 			voiceUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_382954446742605371750230185484.mp3'
		// 		},
		// 		{
		// 			duration: 3,
		// 			captions: [
		// 				{
		// 					text: '지금 바로 득템!',
		// 					startTime: 0.1,
		// 					endTime: 1
		// 				},
		// 				{
		// 					text: '가성비 캐리어는?',
		// 					startTime: 1,
		// 					endTime: 1.8
		// 				},
		// 				{
		// 					text: '앙뜨레!',
		// 					startTime: 1.8,
		// 					endTime: 2.8
		// 				}
		// 			],
		// 			description: '제품 구매 링크 또는 QR 코드를 보여준다. 앙뜨레 로고 강조.',
		// 			voiceUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_72510835382047061750230189786.mp3'
		// 		},
		// 		{
		// 			duration: 4,
		// 			captions: [
		// 				{
		// 					text: '여행 준비 끝!',
		// 					startTime: 0.2,
		// 					endTime: 1
		// 				},
		// 				{
		// 					text: '앙뜨레 캐리어와 함께',
		// 					startTime: 1,
		// 					endTime: 2
		// 				},
		// 				{
		// 					text: '즐거운 여행 되세요!',
		// 					startTime: 2,
		// 					endTime: 3.7
		// 				}
		// 			],
		// 			description: '캐리어를 끌고 여행을 떠나는 행복한 사람들의 모습. 밝고 긍정적인 분위기.',
		// 			voiceUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_90439930380516031750230194621.mp3'
		// 		}
		// 	]
		// });
	});
</script>
