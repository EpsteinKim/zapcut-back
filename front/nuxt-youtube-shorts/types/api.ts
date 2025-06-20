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
