'use client';

import { Button, Card, CardBody, Chip, Typography } from '@material-tailwind/react';

export function Pricing() {
	const pricing = [
		{
			title: '스타터',
			price: '₩미정',
			period: '/월',
			description: '콘텐츠 제작을 시작하는 분들을 위한',
			features: [
				'월 10개 비디오',
				'최대 30초 숏폼',
				'워터마크 없음',
				'AI 자동 자막'
			],
			color: 'blue',
			popular: false
		},
		{
			title: '크리에이터',
			price: '₩미정',
			period: '/월',
			description: '개인 크리에이터를 위한 완벽한 선택',
			features: [
				'월 30개 비디오',
				'최대 1분 숏폼',
				'워터마크 없음',
				'AI 자동 자막'
			],
			color: 'purple',
			popular: true
		}
	];

	return (
		<section className='py-20 px-4'>
			<div className='container mx-auto max-w-4xl'>
				<div className='text-center mb-16'>
					<Typography variant='h2' className='text-3xl md:text-5xl font-bold text-white mb-4'>
						가격은?
					</Typography>
				</div>

				<div className='grid grid-cols-2 md:grid-cols-2 gap-12'>
					{ pricing.map((plan, index) => (
						<Card
							key={ index }
							className={ `relative bg-white/10 backdrop-blur-md border border-white/20 ${ plan.popular ? 'ring-2 ring-purple-500 scale-105' : ''
							}` }
						>
							{ plan.popular && (
								<div className='absolute -top-4 left-1/2 transform -translate-x-1/2'>
									<Chip value='인기' className='bg-gradient-to-r from-purple-500 to-pink-500 text-white' />
								</div>
							) }
							<CardBody className='p-8 text-center'>
								<Typography variant='h4' className='text-white font-bold mb-2'>
									{ plan.title }
								</Typography>
								<Typography className='text-white/80 mb-4'>
									{ plan.description }
								</Typography>
								<div className='mb-6'>
									<Typography variant='h2' className='text-white font-bold'>
										{ plan.price }
										<span className='text-lg text-white/80'>{ plan.period }</span>
									</Typography>
								</div>
								<Button
									fullWidth
									className={ `mb-6 ${ plan.popular
										? 'bg-gradient-to-r from-purple-500 to-pink-500'
										: 'bg-white/20 text-white border border-white/30'
									}` }
								>
									시작하기
								</Button>
								<ul className='space-y-2'>
									{ plan.features.map((feature, featureIndex) => (
										<li key={ featureIndex } className='text-white/80 flex items-center'>
											<Typography className={'mx-auto'}>
												{ feature }
											</Typography>
										</li>
									)) }
								</ul>
							</CardBody>
						</Card>
					)) }
				</div>
			</div>
		</section>
	);
} 