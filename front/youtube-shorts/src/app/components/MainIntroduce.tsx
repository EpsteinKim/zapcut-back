import { Button, Chip, Typography } from '@material-tailwind/react';

export const MainIntroduce = () => {
	return (
		<section className='relative py-20 px-4 text-center'>
			<div className='absolute inset-0 bg-gradient-to-r from-purple-600/20 to-pink-600/20 blur-3xl'></div>
			<div className='container mx-auto relative z-10'>
				<Typography variant='h1' className='text-4xl md:text-6xl font-bold text-white mb-6 leading-tight'>
					상품 소개 및 기타 쇼츠 비디오 생성,<br />
					<span className='bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent'>
						자동으로 채널 성장
					</span>
				</Typography>
				<Typography variant='lead' className='text-xl text-white/80 mb-8'>
					몇 번의 클릭만으로 전문가 수준의 숏 비디오를 제작하세요,
					상품 소개, 상황극, 커뮤니티 비디오를 자동 생성합니다.
				</Typography>
				<div className='flex flex-col sm:flex-row gap-4 justify-center items-center'>
					<Button
						size='lg'
						className='bg-gradient-to-r from-purple-500 to-pink-500 px-8 py-4 text-lg'
					>
						무료로 시작하기
					</Button>
					<Button
						variant='outlined'
						size='lg'
						className='text-white border-white px-8 py-4 text-lg'
					>
						데모 보기
					</Button>
				</div>
			</div>
		</section>
	);
};