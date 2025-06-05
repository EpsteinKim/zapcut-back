'use client';

import { Card, CardBody, Typography } from '@material-tailwind/react';

export function Features() {
    const features = [
        {
            title: 'AI 쇼츠 생성',
            description: '몇 번의 클릭만으로 여러가지 유튜브 쇼츠를 자동 생성하세요.',
            icon: '🎬'
        },
        {
            title: '자동 자막 생성',
            description: '사용자의 입력대로 자막을 생성하거나 자동으로 생성합니다.',
            icon: '📝'
        },
    ];

    return (
        <section className='py-20 px-4'>
            <div className='container mx-auto'>
                <div className='text-center mb-16'>
                    <Typography variant='h2' className='text-3xl md:text-5xl font-bold text-white mb-4'>
                        유튜브 쇼츠를 만드는 가장 빠른 방법
                    </Typography>
                    <Typography className='text-xl text-white/80 max-w-3xl mx-auto'>
                        AI 스토리, 커뮤니티 스토리, 상품 소개, 대화 비디오를 자동으로 생성합니다.
                    </Typography>
                </div>

                <div className='grid grid-cols-2 md:grid-cols-2 gap-6 max-w-3xl mx-auto'>
                    {features.map((feature, index) => (
                        <Card key={index} className='bg-white/10 backdrop-blur-md border border-white/20'>
                            <CardBody className='text-center p-6'>
                                <div className='text-4xl mb-4'>{feature.icon}</div>
                                <Typography variant='h5' className='text-white mb-3 font-semibold'>
                                    {feature.title}
                                </Typography>
                                <Typography className='text-white/80'>
                                    {feature.description}
                                </Typography>
                            </CardBody>
                        </Card>
                    ))}
                </div>
            </div>
        </section>
    );
} 