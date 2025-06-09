import { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://your-domain.com'

    return [
        {
            url: `${baseUrl}/`,
            lastModified: new Date(),
            changeFrequency: 'daily',
            priority: 1,
        },
        // 다른 SEO가 필요한 페이지들은 여기에 추가
        // SPA 페이지들은 의도적으로 포함하지 않음
    ]
} 