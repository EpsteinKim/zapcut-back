import type { Config } from 'tailwindcss'

export default {
	content: [
		'./src/**/*.{js,ts,jsx,tsx,mdx}',
		'./components/**/*.{js,ts,jsx,tsx,mdx}',
		'./app/**/*.{js,ts,jsx,tsx,mdx}',
	],
	theme: {
		extend: {
			colors: {
				gray: {
					900: '#111827',
				},
				purple: {
					900: '#581c87',
					400: '#a855f7',
					500: '#8b5cf6',
					600: '#7c3aed',
				},
				blue: {
					950: '#172554',
				},
				pink: {
					400: '#f472b6',
					500: '#ec4899',
					600: '#db2777',
				}
			}
		}
	},
	plugins: [],
} satisfies Config
