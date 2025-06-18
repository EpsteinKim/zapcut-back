import { defineNuxtPlugin } from '#app';
import { ofetch } from 'ofetch';

type JsonObject = { [key: string]: JsonValue };
type JsonValue = string | number | boolean | null | JsonValue[] | JsonObject;

// 카멜케이스를 스네이크케이스로 변환하는 함수
function toSnakeCase<T extends JsonValue>(obj: T): T {
	if (obj === null || typeof obj !== 'object') {
		return obj;
	}

	if (Array.isArray(obj)) {
		return obj.map((item) => toSnakeCase(item)) as T;
	}

	const result = Object.keys(obj as JsonObject).reduce((acc: JsonObject, key: string) => {
		const snakeKey = key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
		acc[snakeKey] = toSnakeCase((obj as JsonObject)[key]);
		return acc;
	}, {});

	return result as T;
}

// 스네이크케이스를 카멜케이스로 변환하는 함수
function toCamelCase<T extends JsonValue>(obj: T): T {
	if (obj === null || typeof obj !== 'object') {
		return obj;
	}

	if (Array.isArray(obj)) {
		return obj.map((item) => toCamelCase(item)) as T;
	}

	const result = Object.keys(obj as JsonObject).reduce((acc: JsonObject, key: string) => {
		const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
		acc[camelKey] = toCamelCase((obj as JsonObject)[key]);
		return acc;
	}, {});

	return result as T;
}

export default defineNuxtPlugin(() => {
	const config = useRuntimeConfig();
	const apiBaseUrl = config.public.apiBaseUrl as string;

	const customFetch = ofetch.create({
		// 요청 전 처리
		onRequest({ options, request }) {
			// request가 string 또는 URL 객체인 경우만 처리
			const requestUrl = typeof request === 'string' ? request : request instanceof URL ? request.toString() : request?.toString() || '';

			// API 요청인 경우에만 변환 적용 (상대 경로이거나 API 도메인으로 시작하는 경우)
			if (!(requestUrl.startsWith('/') || requestUrl.startsWith(apiBaseUrl))) {
				console.log('Skipping non-API request:', requestUrl);
				return;
			}

			// body가 있는 경우 스네이크케이스로 변환
			if (options.body && typeof options.body === 'string') {
				if (typeof options.body === 'string') {
					try {
						const parsedBody = JSON.parse(options.body);
						if (typeof parsedBody === 'object') {
							options.body = JSON.stringify(toSnakeCase(parsedBody));
						}
					} catch (e) {
						// JSON 파싱에 실패한 경우 원본 문자열 유지
						console.log('Failed to parse body as JSON:', e);
					}
				} else if (typeof options.body === 'object') {
					options.body = toSnakeCase(options.body as JsonObject);
				}
			}

			// query 파라미터가 있는 경우 스네이크케이스로 변환
			if (options.params && typeof options.params === 'object') {
				options.params = toSnakeCase(options.params as JsonObject);
			}
		},
		// 응답 처리
		async onResponse({ response, request }) {
			// request가 string 또는 URL 객체인 경우만 처리
			const requestUrl = typeof request === 'string' ? request : request instanceof URL ? request.toString() : request?.toString() || '';

			// API 요청인 경우에만 변환 적용 (상대 경로이거나 API 도메인으로 시작하는 경우)
			if (!(requestUrl.startsWith('/') || requestUrl.startsWith(apiBaseUrl))) {
				console.log('Skipping non-API response:', requestUrl);
				return;
			}

			// 응답 데이터를 카멜케이스로 변환
			if (response._data && typeof response._data === 'object') {
				console.log('Original response:', response._data);
				response._data = toCamelCase(response._data as JsonObject);
				console.log('Transformed response:', response._data);
			}
		}
	});

	// @ts-expect-error: Nuxt의 $fetch 타입과 완벽하게 일치하지 않지만 실제 동작에는 문제없음
	globalThis.$fetch = customFetch;
});
