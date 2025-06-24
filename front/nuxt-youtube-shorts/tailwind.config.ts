import type { Config } from 'tailwindcss';

export default {
	content: ['./components/**/*.{js,vue,ts,tsx}', './layouts/**/*.{js,vue,ts,tsx}', './pages/**/*.{js,vue,ts,tsx}', './stores/**/*.{js,vue,ts,tsx}'],
	theme: {
		extend: {
			screens: {
				xs: '475px'
			}
			// spacing: {
			// 	'18': '4.5rem',
			// 	'88': '22rem'
			// }
			// fontSize: {
			// 	xs: ['0.75rem', { lineHeight: '1rem' }],
			// 	sm: ['0.875rem', { lineHeight: '1.25rem' }],
			// 	base: ['1rem', { lineHeight: '1.5rem' }],
			// 	lg: ['1.125rem', { lineHeight: '1.75rem' }],
			// 	xl: ['1.25rem', { lineHeight: '1.75rem' }]
			// }
		}
	},
	plugins: []
} as Config;
