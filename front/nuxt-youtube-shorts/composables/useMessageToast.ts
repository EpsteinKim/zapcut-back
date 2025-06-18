export const useMessageToast = () => {
    const toast = useToast()

    const showMessage = (message: string, type?: 'info' | 'success' | 'error' | 'warn') => {
        const title = type === 'info' ? '알림' : type === 'success' ? '성공' : type === 'error' ? '오류' : '알림'
        toast.add({ severity: type || 'info', summary: title, detail: message, life: 5000 })
    }

    return { showMessage, toast }
}