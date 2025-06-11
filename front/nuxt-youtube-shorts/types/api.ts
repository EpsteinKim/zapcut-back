export interface Video {
    id: string;
    title: string;
    description: string;
    url: string;
    thumbnailUrl: string;
    createdAt: string;
    updatedAt: string;
}

export interface Comment {
    id: string;
    videoId: string;
    content: string;
    userId: string;
    userName: string;
    createdAt: string;
    updatedAt: string;
}

export interface ApiResponse<T = unknown> {
    success: boolean;
    message?: string;
    data?: T;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
}

export interface ShortsScriptRequest {
    url: string;
    duration: number;  // 초 단위
}

export interface Caption {
    text: string
    start_time: number
    end_time: number
}

export interface Scene {
    video_url?: string
    image_url?: string
    duration: number
    captions: Caption[]
}

export interface ShortsScript {
    title: string;
    scene: Scene[];
} 