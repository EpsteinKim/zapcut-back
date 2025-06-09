'use client';

import { Button } from "@/components/ui/button";

export const Header = () => {
	return (
		<header className="sticky top-0 bg-gray-900/90 backdrop-blur-sm shadow-none border-0 z-50">
			<div className="flex justify-between items-center px-6 py-4">
				<h1 className="text-2xl font-bold text-white/90">
					Youtube Short AI
				</h1>
				<nav className="flex items-center space-x-6">
					<a href="#" className="cursor-pointer text-white hover:opacity-80 transition-opacity">
						기능
					</a>
					<a href="#" className="cursor-pointer text-white hover:opacity-80 transition-opacity">
						가격
					</a>
					<a href="#" className="cursor-pointer text-white hover:opacity-80 transition-opacity">
						도구
					</a>
					<Button variant={"outline"} className="text-black hover:text-purple-500 hover:opacity-80 transition-opacity">
						로그인
					</Button>
				</nav>
			</div>
		</header>
	);
};