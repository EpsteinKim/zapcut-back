<template>
    <section class="py-20 px-4 bg-black/20">
        <div class="max-w-screen-lg mx-auto">
            <div class="text-center mb-16">
                <h2 class="text-3xl md:text-5xl font-bold text-white mb-4">
                    실제 크리에이터 성공 사례
                </h2>
                <p class="text-xl text-white/80">
                    10,000+ 콘텐츠 크리에이터들의 사랑을 받고 있습니다
                </p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                <Card
v-for="(testimonial, index) in testimonials" :key="index"
                    class="bg-white/10 backdrop-blur-md border-white/20 hover:bg-white/20 transition-colors">
                    <template #content>
                        <div class="p-6">
                            <p class="text-white/90 mb-4 italic">
                                "{{ testimonial.content }}"
                            </p>
                            <div class="flex items-center">
                                <div>
                                    <p class="text-white font-semibold">
                                        {{ testimonial.name }}
                                    </p>
                                    <p class="text-white/70 text-sm">
                                        {{ testimonial.role }}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </template>
                </Card>
            </div>
        </div>
    </section>
</template>

<script setup lang="ts">
import { Card } from '#components'

interface Testimonial {
    name: string
    role: string
    content: string
}

const testimonials: Testimonial[] = [
    {
        name: 'epstein',
        role: '스토리 비디오 크리에이터',
        content: '설명~~~~'
    },
    {
        name: 'epstein2',
        role: '지식 공유자',
        content: '설명'
    },
    {
        name: 'epstein3',
        role: '무서운 스토리 채널 크리에이터',
        content: '설명'
    }
]
</script>