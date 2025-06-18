<template>
	<section class="relative py-20 px-4 text-center">
		<div class="absolute inset-0 bg-linear-to-r from-purple-600/20 to-pink-500/20 blur-3xl" />
		<div class="max-w-screen-lg mx-auto relative z-10">
			<h1 class="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
				상품 소개 및 기타 쇼츠 비디오 생성,
				<br />
				<span class="bg-linear-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">자동으로 채널 성장</span>
			</h1>
			<h2 class="text-xl text-white/80 mb-8">
				몇 번의 클릭만으로 전문가 수준의 숏 비디오를 제작하세요, 상품 소개, 상황극, 커뮤니티 비디오를 자동 생성합니다.
			</h2>
			<div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
				<Button
					label="무료로 시작하기"
					size="large"
					class="bg-linear-to-r! from-purple-500! to-pink-500! text-white border-0! px-8 py-3"
					@click="$router.push('/generate/shorts')"
				/>
			</div>
		</div>
	</section>
</template>
