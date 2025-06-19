import { parseGIF, decompressFrames, type ParsedFrame } from 'gifuct-js';

export const useVideoComposer = () => {
	const blockLoadingStore = useBlockLoadingStore();
	const CANVAS_WIDTH = 1080;
	const CANVAS_HEIGHT = 1920;
	const FPS = 30;

	const calculateImageTransform = (imageWidth: number, imageHeight: number) => {
		const widthRatio = CANVAS_WIDTH / imageWidth;
		const heightRatio = CANVAS_HEIGHT / imageHeight;
		const scaleRatio = Math.min(widthRatio, heightRatio);
		const newWidth = Math.floor(imageWidth * scaleRatio);
		const newHeight = Math.floor(imageHeight * scaleRatio);
		const xCenter = Math.floor((CANVAS_WIDTH - newWidth) / 2);
		const yCenter = Math.floor((CANVAS_HEIGHT - newHeight) / 2);

		return { newWidth, newHeight, xCenter, yCenter };
	};

	const isGifFile = (url: string): boolean => {
		const urlPath = url.split('?')[0];
		return urlPath.toLowerCase().endsWith('.gif');
	};

	const drawErrorScreen = (ctx: CanvasRenderingContext2D) => {
		ctx.fillStyle = 'black';
		ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
		ctx.fillStyle = 'white';
		ctx.font = '30px Arial';
		ctx.fillText('미디어 로딩 실패', CANVAS_WIDTH / 2 - 100, CANVAS_HEIGHT / 2);
	};

	const drawBlackScreen = (ctx: CanvasRenderingContext2D) => {
		ctx.fillStyle = 'black';
		ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
	};

	const drawVideoFrame = (videoElement: HTMLVideoElement, ctx: CanvasRenderingContext2D) => {
		if (videoElement.readyState >= 2) {
			const { newWidth, newHeight, xCenter, yCenter } = calculateImageTransform(videoElement.videoWidth, videoElement.videoHeight);
			ctx.drawImage(videoElement, xCenter, yCenter, newWidth, newHeight);
		}
	};

	const processVideoScene = async (ctx: CanvasRenderingContext2D, scene: Scene, videoCache: Map<string, HTMLVideoElement>) => {
		try {
			const videoElement = videoCache.get(scene.videoUrl!);
			if (!videoElement) {
				throw new Error('비디오 요소를 찾을 수 없습니다');
			}

			const restartVideo = () => {
				videoElement.currentTime = 0;
				videoElement.play();
			};
			videoElement.addEventListener('ended', restartVideo);

			videoElement.play();

			const drawInterval = setInterval(() => drawVideoFrame(videoElement, ctx), 1000 / FPS);
			await delay(scene.duration * 1000);
			clearInterval(drawInterval);
			videoElement.removeEventListener('ended', restartVideo);
			videoElement.pause();
		} catch (error) {
			console.error('비디오 처리 에러:', error);
			drawErrorScreen(ctx);
			await delay(scene.duration * 1000);
		}
	};

	const processGifScene = async (ctx: CanvasRenderingContext2D, scene: Scene, gifCache: Map<string, ParsedFrame[]>) => {
		try {
			const frames = gifCache.get(scene.imageUrl!);
			if (!frames) {
				throw new Error('GIF 프레임을 찾을 수 없습니다');
			}

			const width = frames[0].dims.width;
			const height = frames[0].dims.height;

			const tempCanvas = document.createElement('canvas');
			tempCanvas.width = width;
			tempCanvas.height = height;
			const tempCtx = tempCanvas.getContext('2d');
			assert(tempCtx);

			const sceneEndTime = scene.duration * 1000;

			let accumulatedTime = 0;
			let i = 0;
			while (accumulatedTime < sceneEndTime) {
				tempCtx.clearRect(0, 0, width, height);
				const imageData = tempCtx.createImageData(width, height);
				imageData.data.set(frames[i].patch);
				tempCtx.putImageData(imageData, 0, 0);
				const transform = calculateImageTransform(width, height);
				ctx.drawImage(tempCanvas, transform.xCenter, transform.yCenter, transform.newWidth, transform.newHeight);
				const delayTime = Math.min(frames[i].delay || 20, sceneEndTime - accumulatedTime);
				await delay(delayTime);
				accumulatedTime += delayTime;
				i++;
				if (i >= frames.length) {
					i = 0;
				}
			}
		} catch (error) {
			console.error('GIF 처리 에러:', error);
			drawErrorScreen(ctx);
			await delay(scene.duration * 1000);
		}
	};

	const processImageScene = async (ctx: CanvasRenderingContext2D, scene: Scene, imageCache: Map<string, HTMLImageElement>) => {
		try {
			const img = imageCache.get(scene.imageUrl!);
			if (!img) {
				throw new Error('이미지를 찾을 수 없습니다');
			}

			const drawImage = () => {
				const { newWidth, newHeight, xCenter, yCenter } = calculateImageTransform(img.width, img.height);
				ctx.drawImage(img, xCenter, yCenter, newWidth, newHeight);
				requestAnimationFrame(drawImage);
			};

			const animationID = requestAnimationFrame(drawImage);
			await delay(scene.duration * 1000);
			cancelAnimationFrame(animationID);
		} catch (error) {
			console.error('이미지 처리 에러:', error);
			drawErrorScreen(ctx);
			await delay(scene.duration * 1000);
		}
	};

	const recordCanvas = async (canvas: HTMLCanvasElement, processScenes: () => Promise<void>): Promise<Blob> => {
		const stream = canvas.captureStream(FPS);
		const mediaRecorder = new MediaRecorder(stream, {
			mimeType: 'video/webm;codecs=vp8'
		});

		const chunks: Blob[] = [];
		mediaRecorder.ondataavailable = (e) => {
			if (e.data.size > 0) chunks.push(e.data);
		};

		return new Promise((resolve, reject) => {
			mediaRecorder.onstop = () => {
				resolve(new Blob(chunks, { type: 'video/webm' }));
			};

			mediaRecorder.start();

			processScenes()
				.then(() => mediaRecorder.stop())
				.catch((error) => {
					mediaRecorder.stop();
					reject(error);
				});
		});
	};

	const getComposedVideoBlob = async (script: ShortsScript) => {
		blockLoadingStore.setBlocked(true, '비디오 컴포지션 중...');

		// GIF 파일들을 미리 로드하여 캐시
		const gifCache = new Map<string, ParsedFrame[]>();
		const videoCache = new Map<string, HTMLVideoElement>();
		const imageCache = new Map<string, HTMLImageElement>();

		for (const scene of script.scenes) {
			if (scene.videoUrl) {
				await new Promise((resolve, reject) => {
					const video = document.createElement('video');
					video.crossOrigin = 'anonymous';
					video.src = scene.videoUrl!;
					video.onloadedmetadata = () => {
						videoCache.set(scene.videoUrl!, video);
						resolve(video);
					};
					video.onerror = () => {
						console.error('비디오 로딩 실패:', scene.videoUrl);
						reject(new Error('비디오 로딩 실패'));
					};
				});
			} else if (scene.imageUrl) {
				if (isGifFile(scene.imageUrl)) {
					try {
						const response = await fetch(scene.imageUrl);
						const gifData = await response.arrayBuffer();
						const gif = parseGIF(gifData);
						const frames = decompressFrames(gif, true);
						gifCache.set(scene.imageUrl, frames);
					} catch (error) {
						console.error('GIF 로딩 실패:', scene.imageUrl, error);
					}
				} else {
					await new Promise((resolve, reject) => {
						const img = new Image();
						img.crossOrigin = 'anonymous';
						img.src = scene.imageUrl!;
						img.onload = () => {
							imageCache.set(scene.imageUrl!, img);
							resolve(img);
						};
						img.onerror = () => {
							console.error('이미지 로딩 실패:', scene.imageUrl);
							reject(new Error('이미지 로딩 실패'));
						};
					});
				}
			}
		}

		try {
			const canvas = document.createElement('canvas');
			canvas.width = CANVAS_WIDTH;
			canvas.height = CANVAS_HEIGHT;
			const ctx = canvas.getContext('2d');
			assert(ctx);

			const processAllScenes = async () => {
				const startTime = performance.now();
				for (const scene of script.scenes) {
					if (scene.videoUrl) {
						await processVideoScene(ctx, scene, videoCache);
					} else if (scene.imageUrl) {
						if (isGifFile(scene.imageUrl)) {
							await processGifScene(ctx, scene, gifCache);
						} else {
							await processImageScene(ctx, scene, imageCache);
						}
					} else {
						drawBlackScreen(ctx);
						await delay(scene.duration * 1000);
					}
					drawBlackScreen(ctx);
				}
				const endTime = performance.now();
				console.log(`씬 처리 시간: ${endTime - startTime}ms`);
			};

			const blob = await recordCanvas(canvas, processAllScenes);
			return blob;
		} finally {
			blockLoadingStore.setBlocked(false);
		}
	};

	return { getComposedVideoBlob, calculateImageTransform };
};
