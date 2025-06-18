import { useConfirm } from 'primevue/useconfirm';

export const useConfirmDialog = () => {
	const confirm = useConfirm();

	const showConfirm = (options: {
		message: string;
		header?: string;
		icon?: string;
		acceptLabel?: string;
		rejectLabel?: string;
		acceptClass?: string;
		rejectClass?: string;
	}) => {
		const headerIconMap: Record<string, string> = {
			확인: 'pi pi-question',
			경고: 'pi pi-exclamation-triangle',
			오류: 'pi pi-times-circle',
			성공: 'pi pi-check-circle',
			정보: 'pi pi-info-circle'
		};

		return new Promise<boolean>((resolve) => {
			confirm.require({
				message: options.message,
				header: options.header || '확인',
				icon: options.icon || headerIconMap[options.header || '확인'],
				acceptLabel: options.acceptLabel || '확인',
				rejectLabel: options.rejectLabel || '취소',
				acceptClass: options.acceptClass || 'p-button-primary',
				rejectClass: options.rejectClass || 'p-button-text',
				accept: () => resolve(true),
				reject: () => resolve(false)
			});
		});
	};

	return {
		showConfirm
	};
};
