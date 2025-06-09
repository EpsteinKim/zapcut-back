import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 트레일링 슬래시 제거
  trailingSlash: false,

  // 하이브리드 렌더링: 특정 페이지만 정적 생성
  experimental: {
    // PPR 비활성화 (필요시에만 사용)
    ppr: false,
  },

  // 리다이렉트 설정
  async redirects() {
    return []
  },

  // 검색엔진이 크롤링하지 않을 페이지들을 위한 헤더 설정
  async headers() {
    return [
      {
        // SPA 페이지들에 noindex 헤더 추가
        source: '/view/:path*',
        headers: [
          {
            key: 'X-Robots-Tag',
            value: 'noindex, nofollow',
          },
        ],
      }
    ]
  },
};

export default nextConfig;
