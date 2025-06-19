<template>
	<ScriptGenerator v-if="!shortsStore.script" />
	<VideoEditor v-else />
</template>

<script setup lang="ts">
	const shortsStore = useShortsStore();

	onMounted(() => {
		// shortsStore.setVideoUrl('https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_299234676562700751749732816203.mp4');
		shortsStore.setScript({
			title: '앙뜨레, 눅스, 르네휘테르 올리브영 브랜드 세일 꿀팁!',
			scenes: [
				{
					duration: 2,
					captions: [
						{
							text: '여러분~!',
							startTime: 0.3,
							endTime: 1
						},
						{
							text: '지금 올리브영에서',
							startTime: 1,
							endTime: 1.7
						}
					],
					description: '밝은 표정으로 인사하는 모습. 올리브영 로고가 살짝 보이는 배경.',
					voiceUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_278824333634493551750300152254.mp3',
					imageUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_18512645620810941750300101034.gif'
				},
				{
					duration: 3,
					captions: [
						{
							text: '앙뜨레, 눅스, 르네휘테르',
							startTime: 0.2,
							endTime: 1.2
						},
						{
							text: '브랜드 세일하는 거 알아요?',
							startTime: 1.2,
							endTime: 2.5
						}
					],
					description: '앙뜨레, 눅스, 르네휘테르 제품들이 진열된 모습. 텍스트로 브랜드 이름 강조.',
					voiceUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_189161305130820971750300156814.mp3',
					videoUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_72383348908765431750300101806.mp4'
				},
				{
					duration: 4,
					captions: [
						{
							text: '특히 앙뜨레는',
							startTime: 0.3,
							endTime: 1
						},
						{
							text: '이번 기회에 꼭 득템해야 해!',
							startTime: 1,
							endTime: 2.5
						},
						{
							text: '왜냐면...',
							startTime: 2.5,
							endTime: 3
						}
					],
					description: '앙뜨레 제품(샴푸, 트리트먼트) 클로즈업. 앙뜨레 모델 사진 잠깐 보여주기.',
					voiceUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_34746363013746741750300162173.mp3',
					imageUrl: 'https://youtube-shorts-files.s3.ap-northeast-2.amazonaws.com/1/no_94171528855326651750300102024.jpg'
				}
			]
		});
	});
</script>
