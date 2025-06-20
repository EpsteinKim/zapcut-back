import type { ApiResponse, ShortsScriptRequest, ShortsScript, ShortsVideoRequest } from '~/types/api';
import type { NitroFetchRequest, NitroFetchOptions } from 'nitropack';

// 쿼리 파라미터를 위한 타입 정의
type QueryValue = string | number | boolean | null | undefined;
type QueryParams = Record<string, QueryValue>;

export const useApi = () => {
	const config = useRuntimeConfig();

	const Api = async <T>(endpoint: string, options: Partial<NitroFetchOptions<NitroFetchRequest>> & { query?: QueryParams } = {}) => {
		const { query, ...fetchOptions } = options;
		const baseUrl = config.public.apiBaseUrl + '/api/v1';
		const fullUrl = `${baseUrl}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;

		let apiUrl = fullUrl;
		if (query) {
			const queryString = Object.entries(query)
				.map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
				.join('&');
			apiUrl = `${fullUrl}${queryString ? '?' + queryString : ''}`;
		}

		const response = await $fetch<ApiResponse<T>>(apiUrl, {
			...fetchOptions,
			headers: {
				'Content-Type': 'application/json',
				...fetchOptions.headers
			}
		});

		if (!response.data) {
			throw new Error(response.message ?? 'API 요청 실패');
		}
		return response as { data: T; message?: string };
	};

	const get = async <T>(endpoint: string, query?: QueryParams) => {
		return await Api<T>(endpoint, {
			method: 'GET',
			query
		});
	};

	const post = async <T>(endpoint: string, data?: object) => {
		return await Api<T>(endpoint, {
			method: 'POST',
			body: data ? JSON.stringify(data) : undefined
		});
	};

	const put = async <T>(endpoint: string, data: object) => {
		return await Api<T>(endpoint, {
			method: 'PUT',
			body: JSON.stringify(data)
		});
	};

	const del = async <T>(endpoint: string) => {
		return await Api<T>(endpoint, {
			method: 'DELETE'
		});
	};

	const shorts = {
		generateScript: async (request: ShortsScriptRequest) => {
			const { data } = await post<ShortsScript>('/shorts/scripts', request);
			return data;
		},
		generateVideo: async (request: ShortsVideoRequest) => {
			const { data } = await post<string>('/shorts/video', request);
			return data;
		},
		generateVoice: async (text: string, duration: number): Promise<string> => {
			const { data } = await get<string>('/shorts/voice', { text, duration });
			return data;
		},
		generateImage: async (prompt: string): Promise<string> => {
			const { data } = await get<string>('/shorts/image', { prompt });
			return data;
		}
	};

	return {
		shorts
	};
};
