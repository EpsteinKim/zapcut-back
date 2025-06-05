import withMT from '@material-tailwind/react/utils/withMT';

module.exports = withMT({
	content: ['./pages/**/*.{ts,tsx}'],
	theme: {
		extend: {}
	},
	corePlugins: {
		preflight: false,
	},
	plugins: []
});