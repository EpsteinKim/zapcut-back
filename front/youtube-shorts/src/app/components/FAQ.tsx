'use client';

import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion"

export function FAQ() {
    const faqs = [
        {
            key: 'panel1',
            question: '콘텐츠 스타일을 커스터마이징할 수 있나요?',
            answer: '네, 앞으로 지원하도록 할 예정입니다.'
        },
        {
            key: 'panel2',
            question: '쇼츠 비디오 생성에 얼마나 걸리나요?',
            answer: '비디오 생성은 약 1-2분 정도 소요됩니다.'
        },
        {
            key: 'panel3',
            question: '지원하는 언어는 몇 개인가요?',
            answer: '한국어만 지원합니다.'
        },
    ];

    return (
        <section className="py-20 bg-gradient-to-b from-purple-700 to-purple-600 px-4">
            <div className="max-w-4xl mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">
                        자주 묻는 질문
                    </h2>
                </div>

                <Accordion type="single" collapsible className="space-y-4">
                    {faqs.map((faq) => (
                        <AccordionItem
                            key={faq.key}
                            value={faq.key}
                            className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl px-6 data-[state=open]:bg-white/20"
                        >
                            <AccordionTrigger className="text-white hover:no-underline hover:bg-white/5 py-6 font-medium">
                                {faq.question}
                            </AccordionTrigger>
                            <AccordionContent className="text-white/80 pb-6">
                                {faq.answer}
                            </AccordionContent>
                        </AccordionItem>
                    ))}
                </Accordion>
            </div>
        </section>
    );
} 