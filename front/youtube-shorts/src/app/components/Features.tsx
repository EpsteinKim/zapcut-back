'use client';

import { Card, CardContent } from "@/components/ui/card";

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
        <section className="py-20 px-4">
            <div className="max-w-screen-lg mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">
                        유튜브 쇼츠를 만드는 가장 빠른 방법
                    </h2>
                    <p className="text-xl text-white/80 max-w-3xl mx-auto">
                        AI 스토리, 커뮤니티 스토리, 상품 소개, 대화 비디오를 자동으로 생성합니다.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
                    {features.map((feature, index) => (
                        <Card
                            key={index}
                            className="bg-white/10 backdrop-blur-md border-white/20 hover:bg-white/20 transition-colors"
                        >
                            <CardContent className="text-center p-6">
                                <div className="text-4xl mb-4">{feature.icon}</div>
                                <h3 className="text-white mb-3 font-semibold text-xl">
                                    {feature.title}
                                </h3>
                                <p className="text-white/80">
                                    {feature.description}
                                </p>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        </section>
    );
} 