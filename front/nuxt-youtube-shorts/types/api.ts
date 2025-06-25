export const CaptionAnimationEffect = {
	SEQUENTIAL: 'SEQUENTIAL',
	LARGE_TEXT: 'LARGE_TEXT',
	SMOOTH_POP: 'SMOOTH_POP'
} as const;
export type CaptionAnimationEffect = (typeof CaptionAnimationEffect)[keyof typeof CaptionAnimationEffect];

export const CaptionAnimationEffectInfo: Record<CaptionAnimationEffect, { title: string; description: string }> = {
	[CaptionAnimationEffect.SEQUENTIAL]: {
		title: '순차 생성',
		description: '자막이 순차적으로 생성됩니다.'
	},
	[CaptionAnimationEffect.LARGE_TEXT]: {
		title: '확대 유지 ',
		description: '자막이 확대되고 원래대로 돌아옵니다.'
	},
	[CaptionAnimationEffect.SMOOTH_POP]: {
		title: '스무스 팝',
		description: '자막이 부드럽게 커졌다 돌아갑니다.'
	}
} as const;

export interface ApiResponse<T = unknown> {
	success?: boolean;
	message?: string;
	data?: T;
}

export interface ShortsScriptRequest {
	duration: number; // 초 단위
	title?: string;
	description?: string;
}

export interface Scene {
	videoUrl?: string;
	imageUrl?: string;
	duration: number;
	captions: CaptionInfo[];
	voiceUrl?: string;
	description: string;
	thumbnailUrl?: string; // 여기에서만 씀
}
export interface CaptionInfo {
	text: string;
	startTime: number;
	endTime: number;
	animationEffect?: CaptionAnimationEffect;
	color?: string; // (hex code)
}

export interface ShortsScript {
	title: string;
	scenes: Scene[];
	backgroundMusicUrl?: string;
}

export interface ShortsVideoRequest {
	backgroundMusicUrl?: string;
	musicVolume?: number;
	scenes: Scene[];
}
