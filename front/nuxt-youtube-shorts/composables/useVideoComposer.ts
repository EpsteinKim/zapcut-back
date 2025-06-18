export const useVideoComposer = () => {
	const blockLoadingStore = useBlockLoadingStore();
	const CANVAS_WIDTH = 1080;
	const CANVAS_HEIGHT = 1920;
	const FPS = 30;

	// 캔버스 생성 및 초기화 로직 분리
	const createCanvas = () => {
		const canvas = document.createElement('canvas');
		canvas.width = CANVAS_WIDTH;
		canvas.height = CANVAS_HEIGHT;
		const ctx = canvas.getContext('2d');

		if (!ctx) {
			throw new Error('Canvas context could not be created');
		}

		// 기본 검은 배경 설정
		ctx.fillStyle = 'black';
		ctx.fillRect(0, 0, canvas.width, canvas.height);

		return { canvas, ctx };
	};

	// 미디어 에러 핸들링 로직
	const handleMediaError = (ctx: CanvasRenderingContext2D, sceneDuration: number) => {
		return new Promise<void>((resolve) => {
			// 검은 화면 및 에러 텍스트
			ctx.fillStyle = 'black';
			ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
			ctx.fillStyle = 'white';
			ctx.font = '30px Arial';
			ctx.fillText('미디어 로딩 실패', CANVAS_WIDTH / 2 - 100, CANVAS_HEIGHT / 2);

			// 씬 지속 시간
			setTimeout(resolve, sceneDuration * 1000);
		});
	};

	// 비디오 씬 처리 로직
	const processVideoScene = (videoElement: HTMLVideoElement, ctx: CanvasRenderingContext2D, scene: Scene) => {
		return new Promise<void>((resolveScene) => {
			// CORS 설정을 먼저 설정
			videoElement.crossOrigin = 'anonymous';
			videoElement.preload = 'metadata';
			videoElement.src = scene.videoUrl!;

			const handleVideoPlay = async () => {
				try {
					await videoElement.play();

					// 비디오 크기 조정 및 중앙 정렬 로직
					const videoWidth = videoElement.videoWidth;
					const videoHeight = videoElement.videoHeight;
					const widthRatio = CANVAS_WIDTH / videoWidth;
					const heightRatio = CANVAS_HEIGHT / videoHeight;

					const scaleRatio = Math.min(widthRatio, heightRatio);
					const newWidth = Math.floor(videoWidth * scaleRatio);
					const newHeight = Math.floor(videoHeight * scaleRatio);

					const xCenter = Math.floor((CANVAS_WIDTH - newWidth) / 2);
					const yCenter = Math.floor((CANVAS_HEIGHT - newHeight) / 2);

					// 비디오를 캔버스에 그리기
					const drawVideo = () => {
						if (videoElement.readyState >= 2) {
							// 비디오가 재생 가능한 상태인지 확인
							ctx.fillStyle = 'black';
							ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
							ctx.drawImage(videoElement, xCenter, yCenter, newWidth, newHeight);
						}
					};

					// 씬 지속 시간 동안 비디오 그리기
					const drawInterval = setInterval(drawVideo, 1000 / FPS);

					// 씬 지속 시간 후 정지
					setTimeout(() => {
						clearInterval(drawInterval);
						videoElement.pause();
						resolveScene();
					}, scene.duration * 1000);
				} catch (playError) {
					console.error('비디오 재생 에러:', playError);
					await handleMediaError(ctx, scene.duration);
					resolveScene();
				}
			};

			videoElement.onloadedmetadata = () => {
				handleVideoPlay().catch(async (error) => {
					console.error('비디오 재생 준비 에러:', error);
					await handleMediaError(ctx, scene.duration);
					resolveScene();
				});
			};

			// 메타데이터 로딩 실패 시
			videoElement.onerror = async () => {
				console.error('비디오 로딩 에러:', videoElement.error);

				// CORS 에러일 경우 대안적인 방법 시도
				if (videoElement.error?.code === 4) {
					console.log('CORS 에러 감지, 대안적인 방법으로 재시도...');
					try {
						// fetch로 blob을 가져와서 Object URL 생성
						const response = await fetch(scene.videoUrl!, {
							mode: 'no-cors'
						});
						const blob = await response.blob();
						const objectUrl = URL.createObjectURL(blob);

						videoElement.src = objectUrl;
						return; // 재시도하므로 resolveScene 호출하지 않음
					} catch (fetchError) {
						console.error('Fetch 재시도도 실패:', fetchError);
					}
				}

				await handleMediaError(ctx, scene.duration);
				resolveScene();
			};
		});
	};

	// 이미지 씬 처리 로직
	const processImageScene = (ctx: CanvasRenderingContext2D, scene: Scene) => {
		return new Promise<void>((resolveScene) => {
			const img = new Image();
			img.crossOrigin = 'anonymous'; // CORS 설정 추가
			img.src = scene.imageUrl!;

			img.onload = () => {
				// 이미지 크기 조정 및 중앙 정렬 로직
				const imageWidth = img.width;
				const imageHeight = img.height;
				const widthRatio = CANVAS_WIDTH / imageWidth;
				const heightRatio = CANVAS_HEIGHT / imageHeight;

				const scaleRatio = Math.min(widthRatio, heightRatio);
				const newWidth = Math.floor(imageWidth * scaleRatio);
				const newHeight = Math.floor(imageHeight * scaleRatio);

				const xCenter = Math.floor((CANVAS_WIDTH - newWidth) / 2);
				const yCenter = Math.floor((CANVAS_HEIGHT - newHeight) / 2);

				// 검은 배경 채우기
				ctx.fillStyle = 'black';
				ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

				// 이미지를 중앙에 그리기
				ctx.drawImage(img, xCenter, yCenter, newWidth, newHeight);

				// 이미지 지속 시간
				setTimeout(resolveScene, scene.duration * 1000);
			};

			// 이미지 로딩 실패 시
			img.onerror = async () => {
				console.error('이미지 로딩 에러');
				await handleMediaError(ctx, scene.duration);
				resolveScene();
			};
		});
	};

	// 검은 화면 씬 처리 로직
	const processBlackScene = (ctx: CanvasRenderingContext2D, scene: Scene) => {
		return new Promise<void>((resolveScene) => {
			ctx.fillStyle = 'black';
			ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

			// 씬 지속 시간
			setTimeout(resolveScene, scene.duration * 1000);
		});
	};

	const getComposedVideoBlob = async (script: ShortsScript) => {
		blockLoadingStore.setBlocked(true, '비디오 컴포지션 중...');
		const { canvas, ctx } = createCanvas();
		const videoElement = document.createElement('video');
		videoElement.muted = true;
		videoElement.playsInline = true; // iOS 지원을 위해 추가

		// 미디어 레코더 설정
		const stream = canvas.captureStream(FPS);
		const mediaRecorder = new MediaRecorder(stream, {
			mimeType: 'video/webm;codecs=vp8' // 브라우저 호환성을 위해 WebM 형식 사용
		});

		const chunks: Blob[] = [];
		mediaRecorder.ondataavailable = (e) => {
			if (e.data.size > 0) chunks.push(e.data);
		};

		const blob = await new Promise<Blob>((resolve, reject) => {
			mediaRecorder.onstop = () => {
				const blob = new Blob(chunks, { type: 'video/webm' });
				resolve(blob);
			};

			mediaRecorder.start();

			const processScenes = async () => {
				try {
					for (const scene of script.scenes) {
						if (scene.videoUrl) {
							await processVideoScene(videoElement, ctx, scene);
						} else if (scene.imageUrl) {
							await processImageScene(ctx, scene);
						} else {
							await processBlackScene(ctx, scene);
						}
					}
					// 전체 duration과 현재까지 처리된 시간의 차이를 계산
					const totalProcessedTime = script.scenes.reduce((acc, scene) => acc + scene.duration, 0);
					const totalDuration = script.scenes.reduce((acc, scene) => acc + scene.duration, 0);
					const remainingTime = totalDuration - totalProcessedTime;

					// 남은 시간이 있다면 검은 화면으로 채우기
					if (remainingTime > 0) {
						await processBlackScene(ctx, { duration: remainingTime } as Scene);
					}
					mediaRecorder.stop();
				} catch (error) {
					console.error('비디오 컴포지션 중 전체 에러:', error);
					mediaRecorder.stop();
					reject(error);
				}
			};

			processScenes().catch(reject);
		});
		blockLoadingStore.setBlocked(false);
		return blob;
	};

	return { getComposedVideoBlob };
};
