import Aura from '@primeuix/themes/aura';

export default defineNuxtConfig({
  compatibilityDate: '2025-05-15',
  devtools: { enabled: true },

  // 컴포넌트 자동 import 설정
  components: {
    dirs: [
      {
        path: '~/components',
        pathPrefix: false,
      },
    ],
  },

  modules: [
    '@nuxt/fonts',
    '@nuxt/eslint',
    '@nuxt/icon',
    '@nuxt/image',
    '@nuxt/scripts',
    '@primevue/nuxt-module',
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt'
  ],
  pinia: {
    storesDirs: ['./stores/**']
  },

  routeRules: {
    '/': { ssr: true, prerender: true },
    '/**': { ssr: false }
  },

  // Vue SFC 설정
  vue: {
    compilerOptions: {
      isCustomElement: (tag) => ['BUTTON', 'DIV'].includes(tag)
    }
  },

  vite: {
    plugins: []
  },

  primevue: {
    options: {
      theme: {
        preset: Aura,
        options: {
          prefix: 'p',
          darkModeSelector: 'light',
          cssLayer: false
        }
      }
    },
    components: {
      exclude: ['Form', 'FormField']
    }
  },

  css: ['~/assets/css/main.css', 'primeicons/primeicons.css'],

  postcss: {
    plugins: {
      '@tailwindcss/postcss': {},
    },
  },

  app: {
    head: {
      title: 'Youtube Shorts AI - AI로 자동 생성하는 유튜브 쇼츠',
      htmlAttrs: {
        lang: 'ko'
      },
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=Inter:wght@400;500;600;700&display=swap' }
      ],
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { key: 'description', name: 'description', content: 'AI로 자동 생성하는 YouTube Shorts - 상품 소개, 스토리 비디오를 몇 번의 클릭으로 전문가 수준으로 제작하세요' },
        { name: 'keywords', content: '유튜브 쇼츠, AI 비디오, 자동 생성, 상품 소개, 스토리 비디오, 콘텐츠 제작' },
        { name: 'author', content: 'Youtube Shorts AI' },
        { name: 'robots', content: 'index, follow' },

        // Open Graph / Facebook
        { property: 'og:type', content: 'website' },
        { property: 'og:title', content: 'Youtube Shorts AI - AI로 자동 생성하는 유튜브 쇼츠' },
        { property: 'og:description', content: 'AI로 자동 생성하는 YouTube Shorts - 상품 소개, 스토리 비디오를 몇 번의 클릭으로 전문가 수준으로 제작하세요' },
        { property: 'og:locale', content: 'ko_KR' },

        // Twitter
        { name: 'twitter:card', content: 'summary_large_image' },
        { name: 'twitter:title', content: 'Youtube Shorts AI - AI로 자동 생성하는 유튜브 쇼츠' },
        { name: 'twitter:description', content: 'AI로 자동 생성하는 YouTube Shorts - 상품 소개, 스토리 비디오를 몇 번의 클릭으로 전문가 수준으로 제작하세요' }
      ]
    }
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:3000/api'
    }
  }
})