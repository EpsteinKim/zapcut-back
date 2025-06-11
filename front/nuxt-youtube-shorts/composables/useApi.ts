import type { ApiResponse, ShortsScriptRequest, ShortsScript } from '~/types/api'
import type { NitroFetchRequest, NitroFetchOptions } from 'nitropack'

// 쿼리 파라미터를 위한 타입 정의
type QueryValue = string | number | boolean | null | undefined
type QueryParams = Record<string, QueryValue>

export const useApi = () => {
    const config = useRuntimeConfig()

    const Api = async <T>(
        endpoint: string,
        options: Partial<NitroFetchOptions<NitroFetchRequest>> & { query?: QueryParams } = {}
    ) => {
        const { query, ...fetchOptions } = options
        const baseUrl = config.public.apiBase + '/api/v1'
        const fullUrl = `${baseUrl}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`

        let apiUrl = fullUrl
        if (query) {
            const queryString = Object.entries(query)
                .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
                .join('&')
            apiUrl = `${fullUrl}${queryString ? '?' + queryString : ''}`
        }

        return await $fetch<ApiResponse<T>>(apiUrl, {
            ...fetchOptions,
            headers: {
                'Content-Type': 'application/json',
                ...fetchOptions.headers
            }
        })
    }

    // 기본 HTTP 메서드별 요청 함수
    const get = async <T>(endpoint: string, query?: QueryParams) => {
        return await Api<T>(endpoint, {
            method: 'GET',
            query
        })
    }

    const post = async <T>(endpoint: string, data?: Record<string, unknown>) => {
        return await Api<T>(endpoint, {
            method: 'POST',
            body: data ? JSON.stringify(data) : undefined
        })
    }

    const put = async <T>(endpoint: string, data: Record<string, unknown>) => {
        return await Api<T>(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        })
    }

    const del = async <T>(endpoint: string) => {
        return await Api<T>(endpoint, {
            method: 'DELETE'
        })
    }

    const shorts = {
        generateScript: async (params: ShortsScriptRequest) => {
            const { data } = await get<ShortsScript>('/shorts/scripts', {
                url: params.url,
                duration: params.duration
            })
            return data
        }
    }

    return {
        shorts
    }
} 