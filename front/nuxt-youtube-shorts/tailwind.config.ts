import type { Config } from 'tailwindcss';

export default {
	content: ['./components/**/*.{js,vue,ts,tsx}', './layouts/**/*.{js,vue,ts,tsx}', './pages/**/*.{js,vue,ts,tsx}', './stores/**/*.{js,vue,ts,tsx}'],
	theme: {
		extend: {
			screens: {
				xs: '475px',
				sm: '640px',
				md: '768px',
				lg: '1024px',
				'lg-plus': '1072px',
				xl: '1280px',
				'2xl': '1536px'
			},
			colors: {
				gray: {
					900: '#111827'
				},
				purple: {
					900: '#581c87',
					400: '#a855f7',
					500: '#8b5cf6',
					600: '#7c3aed'
				},
				blue: {
					950: '#172554'
				},
				pink: {
					400: '#f472b6',
					500: '#ec4899',
					600: '#db2777'
				}
			},
			spacing: {
				'18': '4.5rem',
				'88': '22rem'
			},
			fontSize: {
				xs: ['0.75rem', { lineHeight: '1rem' }],
				sm: ['0.875rem', { lineHeight: '1.25rem' }],
				base: ['1rem', { lineHeight: '1.5rem' }],
				lg: ['1.125rem', { lineHeight: '1.75rem' }],
				xl: ['1.25rem', { lineHeight: '1.75rem' }]
			}
		}
	},
	plugins: []
} as Config;
