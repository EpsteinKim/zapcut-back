import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', {
    state: () => ({
        isDarkMode: true,
        primaryColor: '#3B82F6',
        accentColor: '#10B981'
    }),

    actions: {
        toggleDarkMode() {
            this.isDarkMode = !this.isDarkMode
        },
        setPrimaryColor(color: string) {
            this.primaryColor = color
        }
    }
}) 