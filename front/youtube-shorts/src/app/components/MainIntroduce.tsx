import { Button } from "@/components/ui/button";

export const MainIntroduce = () => {
	return (
		<section className="relative py-20 px-4 text-center">
			<div className="absolute inset-0 bg-feature-gradient blur-3xl"></div>
			<div className="max-w-screen-lg mx-auto relative z-10">
				<h1 className="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
					상품 소개 및 기타 쇼츠 비디오 생성,<br />
					<span className="text-gradient">
						자동으로 채널 성장
					</span>
				</h1>
				<h2 className="text-xl text-white/80 mb-8">
					몇 번의 클릭만으로 전문가 수준의 숏 비디오를 제작하세요,
					상품 소개, 상황극, 커뮤니티 비디오를 자동 생성합니다.
				</h2>
				<div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
					<Button size="lg" className="bg-button-gradient text-white hover:shadow-lg border-0">
						무료로 시작하기
					</Button>
					<Button variant="secondary" size="lg" className="border-white bg-feature-gradient text-white">
						데모 보기
					</Button>
				</div>
			</div>
		</section>
	);
};