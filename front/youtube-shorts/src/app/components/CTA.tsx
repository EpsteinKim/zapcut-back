'use client';

import { Button, Typography } from '@material-tailwind/react';

export function CTA() {
    return (
        <section className='py-20 px-4'>
            <div className='container mx-auto text-center'>
                <Typography variant='h2' className='text-3xl md:text-5xl font-bold text-white mb-6'>
                    몇 번의 클릭으로 바이럴하세요
                </Typography>
                <Typography className='text-xl text-white/80 mb-8 max-w-3xl mx-auto'>
                    AI로 편집된 매일 숏 비디오를 게시하여 청중을 늘리고 최대 참여를 위해 설계하세요.
                    오늘 무료 비디오를 받아보세요.
                </Typography>
                <Button
                    size='lg'
                    className='bg-gradient-to-r from-purple-500 to-pink-500 px-10 py-4 text-lg'
                >
                    무료로 시작하기
                </Button>
            </div>
        </section>
    );
} 