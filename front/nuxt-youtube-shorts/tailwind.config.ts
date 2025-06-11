import type { Config } from 'tailwindcss'

export default {
    content: [
        './components/**/*.{js,vue,ts,tsx}',
        './layouts/**/*.{js,vue,ts,tsx}',
        './pages/**/*.{js,vue,ts,tsx}',
        './stores/**/*.{js,vue,ts,tsx}',
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
} as Config 