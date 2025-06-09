'use client';

import { Button } from "@/components/ui/button";

export function CTA() {
    return (
        <section className="py-20 px-4">
            <div className="max-w-screen-lg mx-auto text-center">
                <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
                    몇 번의 클릭으로 바이럴하세요
                </h2>
                <p className="text-xl text-white/80 mb-8 max-w-3xl mx-auto">
                    AI로 편집된 매일 숏 비디오를 게시하여 청중을 늘리고 최대 참여를 위해 설계하세요.
                    오늘 무료 비디오를 받아보세요.
                </p>
                <Button size="lg" className="bg-button-gradient text-white">
                    무료로 시작하기
                </Button>
            </div>
        </section>
    );
} 