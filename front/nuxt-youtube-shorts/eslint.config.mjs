// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt({
	rules: {
		'@typescript-eslint/no-explicit-any': 'error',
		"@typescript-eslint/no-unused-vars": "warn",
		'vue/html-self-closing': 'off',
		'vue/no-multiple-template-root': 'off'
	}
})
