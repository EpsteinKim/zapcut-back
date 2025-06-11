<template>
    <section class="py-20 px-4">
        <div class="max-w-4xl mx-auto">
            <div class="text-center mb-16">
                <h2 class="text-3xl md:text-5xl font-bold text-white mb-4">
                    자주 묻는 질문
                </h2>
            </div>

            <Accordion value="0" class="space-y-4">
                <AccordionPanel
v-for="(faq, index) in faqs" :key="index" :value="index.toString()"
                    class="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl px-6">
                    <AccordionHeader
                        class="text-white hover:no-underline hover:bg-white/5 py-6 font-medium w-full text-left">
                        {{ faq.question }}
                    </AccordionHeader>
                    <AccordionContent class="text-white/80 pb-6">
                        {{ faq.answer }}
                    </AccordionContent>
                </AccordionPanel>
            </Accordion>
        </div>
    </section>
</template>

<script setup lang="ts">
import { Accordion, AccordionPanel, AccordionHeader, AccordionContent } from '#components'

interface FAQ {
    question: string
    answer: string
}

const faqs: FAQ[] = [
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
]
</script>