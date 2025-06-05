'use client';

import { Accordion, AccordionBody, AccordionHeader, Typography } from '@material-tailwind/react';
import { useState } from 'react';

export function FAQ() {
    const [openAccordion, setOpenAccordion] = useState(0);

    const handleAccordionOpen = (value: number) => {
		console.log(value)
        setOpenAccordion(openAccordion === value ? 0 : value);
    };

    const faqs = [
        {
            question: '콘텐츠 스타일을 커스터마이징할 수 있나요?',
            answer: '네, 앞으로 지원하도록 할 예정입니다.'
        },
        {
            question: '쇼츠 비디오 생성에 얼마나 걸리나요?',
            answer: '비디오 생성은 약 1-2분 정도 소요됩니다.'
        },
        {
            question: '지원하는 언어는 몇 개인가요?',
            answer: '한국어만 지원합니다.'
        },
    ];

    return (
        <section className='py-20 bg-gradient-to-b bg-purple px-4'>
            <div className='container mx-auto max-w-4xl'>
                <div className='text-center mb-16'>
                    <Typography variant='h2' className='text-3xl md:text-5xl font-bold text-white mb-4'>
                        자주 묻는 질문
                    </Typography>
                </div>

                <div className='space-y-4'>
                    {faqs.map((faq, index) => (
                        <Accordion
                            key={index}
                            open={openAccordion === index + 1}
                            className='bg-white/10 backdrop-blur-md border border-white/20 rounded-lg'
                        >
                            <AccordionHeader
                                onClick={() => handleAccordionOpen(index + 1)}
                                className='text-white hover:text-white/80 px-6'
                            >
                                {faq.question}
                            </AccordionHeader>
                            <AccordionBody className='text-white/80 px-6'>
                                {faq.answer}
                            </AccordionBody>
                        </Accordion>
                    ))}
                </div>
            </div>
        </section>
    );
} 