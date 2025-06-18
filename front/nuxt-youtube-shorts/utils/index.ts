export function formatTime(seconds: number) {
	const mins = Math.floor(seconds / 60);
	const secs = Math.floor(seconds % 60);
	return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function getErrorMessage(error: any): string {
	let errorMessage = '';

	if (error?.response?._data?.message) {
		errorMessage = error.response._data.message;
	} else if (error?.message) {
		errorMessage = error.message;
	} else if (error instanceof Error) {
		errorMessage = error.message;
	} else if (typeof error === 'string') {
		errorMessage = error;
	}
	return errorMessage.substring(0, 500);
}
export function playVoice(url: string) {
	const audio = new Audio(url);
	audio.play();
}

export function isValidFileType(mimeType: string): boolean {
	return ALLOWED_MIME_TYPES.includes(mimeType as (typeof ALLOWED_MIME_TYPES)[number]);
}

export function getFileExtensionFromMimeType(mimeType: string): string {
	const mimeToExt: { [key: string]: string } = {
		'image/jpeg': 'jpg',
		'image/png': 'png',
		'image/gif': 'gif',
		'image/webp': 'webp',
		'image/svg+xml': 'svg',
		'video/mp4': 'mp4',
		'video/webm': 'webm',
		'video/quicktime': 'mov',
		'video/x-msvideo': 'avi',
		'audio/mpeg': 'mp3',
		'audio/wav': 'wav',
		'audio/ogg': 'ogg',
		'audio/mp4': 'm4a'
	};

	return mimeToExt[mimeType] || 'bin';
}

export async function uploadToS3(file: File | Blob, userId: string, onProgress?: (percent: number) => void) {
	//eslint-disable-next-line
	return new Promise<string>(async (resolve, reject) => {
		try {
			// File 타입인 경우 Blob으로 변환
			const blob = file instanceof File ? new Blob([await file.arrayBuffer()], { type: file.type }) : file;
			const mimeType = blob.type || 'application/octet-stream';

			// 파일 타입 검증
			if (!isValidFileType(mimeType)) {
				throw new Error('지원하지 않는 파일 형식입니다. 이미지, 비디오, 오디오 파일만 업로드 가능합니다.');
			}

			const fileExtension = getFileExtensionFromMimeType(mimeType);
			const apiUrl = `https://ttxbh6wm8f.execute-api.ap-northeast-2.amazonaws.com/prod/upload/${userId}/no_file.${fileExtension}`;

			const res = await fetch(apiUrl);
			const data = await res.json();
			const uploadUrl = data.uploadUrl;
			const contentType = data.contentType || mimeType;

			// XMLHttpRequest로 업로드
			const xhr = new XMLHttpRequest();
			xhr.open('PUT', uploadUrl, true);
			xhr.setRequestHeader('Content-Type', contentType);

			xhr.upload.onprogress = (event) => {
				if (event.lengthComputable && onProgress) {
					const percent = Math.round((event.loaded * 100) / event.total);
					onProgress(percent);
				}
			};

			xhr.onload = () => {
				if (xhr.status >= 200 && xhr.status < 300) {
					resolve(uploadUrl.split('?')[0]);
				} else {
					reject(new Error(`파일 업로드에 실패했습니다: ${xhr.status} ${xhr.statusText}`));
				}
			};

			xhr.onerror = () => {
				reject(new Error('파일 업로드 중 네트워크 오류가 발생했습니다.'));
			};

			xhr.send(blob);
		} catch (error) {
			reject(error);
		}
	});
}

export function getFileExtension(filename: string): string {
	return filename.split('.').pop()?.toLowerCase() || '';
}
