'use client'

import '@/app/globals.css'
import { Button } from "@/components/ui/button";

export default function Page() {
	return (
		<div className="p-8">
			<h1 className="text-4xl font-bold mb-6">
				Hello NextJs with shadcn/ui!
			</h1>

			<div className="space-y-6">
				<div>
					<p className="text-gray-600 mb-2">
						기본 Button:
					</p>
					<Button>
						기본 버튼
					</Button>
				</div>

				<div>
					<p className="text-gray-600 mb-2">
						Primary Button:
					</p>
					<Button variant="default">
						파란색 버튼
					</Button>
				</div>

				<div>
					<p className="text-gray-600 mb-2">
						Outlined Button:
					</p>
					<Button variant="outline">
						Outlined Button
					</Button>
				</div>

				<div>
					<p className="text-gray-600 mb-2">
						Secondary Button:
					</p>
					<Button variant="secondary">
						Secondary Button
					</Button>
				</div>

				<div>
					<p className="text-gray-600 mb-2">
						Destructive Button:
					</p>
					<Button variant="destructive">
						Destructive Button
					</Button>
				</div>

				<div>
					<p className="text-gray-600 mb-2">
						Ghost Button:
					</p>
					<Button variant="ghost">
						Ghost Button
					</Button>
				</div>

				<div>
					<p className="text-gray-600 mb-2">
						Link Button:
					</p>
					<Button variant="link">
						Link Button
					</Button>
				</div>

				<div>
					<p className="text-gray-600 mb-2">
						다양한 크기의 버튼들:
					</p>
					<div className="flex space-x-4 items-center">
						<Button size="sm" variant="default">
							Small
						</Button>
						<Button size="default" variant="secondary">
							Default
						</Button>
						<Button size="lg" variant="destructive">
							Large
						</Button>
					</div>
				</div>

				<div>
					<p className="text-gray-600 mb-2">
						비활성화된 버튼:
					</p>
					<Button disabled>
						Disabled Button
					</Button>
				</div>
			</div>
		</div>
	);
}