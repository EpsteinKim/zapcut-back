<template>
    <section class="py-20 px-4">
        <div class="max-w-screen-lg mx-auto">
            <div class="text-center mb-16">
                <h2 class="text-3xl md:text-5xl font-bold text-white mb-4">
                    가격은?
                </h2>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-12 max-w-4xl mx-auto">
                <Card
v-for="(plan, index) in pricing" :key="index" :class="[
                    'relative bg-white/10 backdrop-blur-md border-white/20 hover:bg-white/20 transition-colors',
                    { 'ring-2 ring-purple-500 scale-105': plan.popular }
                ]">
                    <template #content>
                        <div class="p-8 text-center">
                            <div v-if="plan.popular" class="absolute -top-3 left-1/2 transform -translate-x-1/2">
                                <Badge
value="인기"
                                    class="bg-linear-to-r from-purple-500 to-pink-500 text-white text-lg" />
                            </div>

                            <h3 class="text-white font-bold mb-2 text-2xl">
                                {{ plan.title }}
                            </h3>
                            <p class="text-white/80 mb-4">
                                {{ plan.description }}
                            </p>
                            <div class="mb-6">
                                <span class="text-white font-bold text-4xl">
                                    {{ plan.price }}
                                    <span class="text-lg text-white/80">
                                        {{ plan.period }}
                                    </span>
                                </span>
                            </div>
                            <Button
label="시작하기" :class="[
                                'w-full mb-6',
                                plan.popular
                                    ? 'bg-linear-to-r from-purple-500 to-pink-500 text-white hover:shadow-lg'
                                    : 'bg-white/20 text-white border border-white/30 hover:bg-white/30'
                            ]" :outlined="!plan.popular" />
                            <ul class="space-y-2">
                                <li
v-for="(feature, featureIndex) in plan.features" :key="featureIndex"
                                    class="text-white/80 flex items-center justify-center">
                                    {{ feature }}
                                </li>
                            </ul>
                        </div>
                    </template>
                </Card>
            </div>
        </div>
    </section>
</template>

<script setup lang="ts">
import { Card, Button, Badge } from '#components'

interface PricingPlan {
    title: string
    price: string
    period: string
    description: string
    features: string[]
    color: string
    popular: boolean
}

const pricing: PricingPlan[] = [
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
]
</script>