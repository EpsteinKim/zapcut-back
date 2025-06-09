'use client';

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

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
		<section className="py-20 px-4">
			<div className="max-w-screen-lg mx-auto">
				<div className="text-center mb-16">
					<h2 className="text-3xl md:text-5xl font-bold text-white mb-4">
						가격은?
					</h2>
				</div>

				<div className="grid grid-cols-1 md:grid-cols-2 gap-12 max-w-4xl mx-auto">
					{pricing.map((plan, index) => (
						<Card
							key={index}
							className={`relative bg-white/10 backdrop-blur-md border-white/20 hover:bg-white/20 transition-colors ${plan.popular ? 'ring-2 ring-purple-500 scale-105' : ''}`}
						>
							{plan.popular && (
								<div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
									<Badge className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
										인기
									</Badge>
								</div>
							)}
							<CardContent className="p-8 text-center">
								<h3 className="text-white font-bold mb-2 text-2xl">
									{plan.title}
								</h3>
								<p className="text-white/80 mb-4">
									{plan.description}
								</p>
								<div className="mb-6">
									<span className="text-white font-bold text-4xl">
										{plan.price}
										<span className="text-lg text-white/80">
											{plan.period}
										</span>
									</span>
								</div>
								<Button
									className={`w-full mb-6 ${plan.popular
										? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:shadow-lg'
										: 'bg-white/20 text-white border border-white/30 hover:bg-white/30'
										}`}
									variant={plan.popular ? "default" : "outline"}
								>
									시작하기
								</Button>
								<ul className="space-y-2">
									{plan.features.map((feature, featureIndex) => (
										<li
											key={featureIndex}
											className="text-white/80 flex items-center justify-center"
										>
											{feature}
										</li>
									))}
								</ul>
							</CardContent>
						</Card>
					))}
				</div>
			</div>
		</section>
	);
} 