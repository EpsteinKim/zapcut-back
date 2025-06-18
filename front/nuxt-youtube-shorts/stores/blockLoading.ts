export const useBlockLoadingStore = defineStore('blockLoading', () => {
	const isBlocked = ref(false);
	const text = ref('');

	const setBlocked = (value: boolean, message?: string) => {
		isBlocked.value = value;
		text.value = message || '';
	};

	return {
		isBlocked,
		text,
		setBlocked
	};
});
