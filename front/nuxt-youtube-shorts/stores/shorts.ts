import { defineStore } from 'pinia';
import type { ShortsScript, ShortsScriptRequest } from '~/types/api';

interface ShortsScriptResponse {
    message: string;
    data: {
        title: string;
        scene: ShortsScript['scene'];
    }
}

export const useShortsStore = defineStore('shorts', () => {
    const api = useApi();

    // 로딩 및 에러 상태
    const isLoading = ref(false);
    const error = ref<string | null>(null);

    // 비디오 상태
    const videoUrl = ref<string>('');
    const currentTime = ref(0);
    const duration = ref(0);
    const isPlaying = ref(false);
    const isMuted = ref(true);
    const playbackSpeed = ref(1);

    // 스크립트 상태
    const script = ref<ShortsScriptResponse['data'] | null>(null);

    // 샘플 데이터
    const sample = {
        "message": "요청이 성공적으로 처리되었습니다.",
        "data": {
            "title": "고급스러움 한도 초과! 라뒤레 손수건 언박싱✨",
            "scene": [
                {
                    "duration": 2,
                    "text": "라뒤레(LADUREE) 손수건 택배 상자 클로즈업",
                    "captions": [
                        {
                            "text": "어머, 이건 뭐야?!",
                            "start_time": 0.5,
                            "end_time": 1.5
                        }
                    ]
                },
                {
                    "duration": 4,
                    "text": "라뒤레 손수건 포장 뜯는 모습 (리본, 포장지 등)",
                    "captions": [
                        {
                            "text": "고급스러움이 뚝뚝!",
                            "start_time": 0.5,
                            "end_time": 1.5
                        },
                        {
                            "text": "선물 받은 기분🎁",
                            "start_time": 2,
                            "end_time": 3
                        }
                    ]
                },
                {
                    "duration": 5,
                    "text": "손수건 펼쳐서 보여주기 (색감, 디자인 강조). 은은한 광택이 도는 고급스러운 재질 표현",
                    "captions": [
                        {
                            "text": "색감 미쳤다…💖",
                            "start_time": 0.5,
                            "end_time": 1.5
                        },
                        {
                            "text": "라이트 그레이 & 핑크 조합!",
                            "start_time": 2,
                            "end_time": 3.5
                        }
                    ]
                },
                {
                    "duration": 5,
                    "text": "손수건 패턴 자세히 보여주기 (도트, 새). 자수로 고급스러움을 더함",
                    "captions": [
                        {
                            "text": "귀여운 도트 & 새 패턴🕊️",
                            "start_time": 0.5,
                            "end_time": 2
                        },
                        {
                            "text": "완전 내 스타일이야!",
                            "start_time": 2.5,
                            "end_time": 3.5
                        }
                    ]
                },
                {
                    "duration": 4,
                    "text": "손으로 손수건 재질 느껴보기. 부드러운 촉감 강조",
                    "captions": [
                        {
                            "text": "촉감도 부드러워🥰",
                            "start_time": 0.5,
                            "end_time": 1.5
                        },
                        {
                            "text": "역시 면 100%!",
                            "start_time": 2,
                            "end_time": 3
                        }
                    ]
                },
                {
                    "duration": 5,
                    "text": "손수건 접어서 가방에 넣는 모습. 휴대하기 좋은 사이즈임을 보여줌",
                    "captions": [
                        {
                            "text": "가방에 쏙 넣어 다니기👜",
                            "start_time": 0.5,
                            "end_time": 2
                        },
                        {
                            "text": "데일리템으로 딱!",
                            "start_time": 2.5,
                            "end_time": 3.5
                        }
                    ]
                },
                {
                    "duration": 5,
                    "text": "손수건 들고 포즈 취하기. 만족스러운 표정 🥰",
                    "captions": [
                        {
                            "text": "특별한 날, 나를 위한 선물🎁",
                            "start_time": 0.5,
                            "end_time": 2
                        },
                        {
                            "text": "라뒤레 손수건 추천💖",
                            "start_time": 2.5,
                            "end_time": 3.5
                        }
                    ]
                }
            ]
        }
    }
    script.value = sample.data

    // 비디오 컨트롤 메서드
    const setTime = (time: number) => {
        currentTime.value = time;
    };

    const setDuration = (time: number) => {
        duration.value = time;
    };

    const togglePlay = () => {
        isPlaying.value = !isPlaying.value;
    };

    const toggleMute = () => {
        isMuted.value = !isMuted.value;
    };

    const setPlaybackSpeed = (speed: number) => {
        playbackSpeed.value = speed;
    };

    const seekRelative = (offset: number) => {
        currentTime.value = Math.max(0, Math.min(currentTime.value + offset, duration.value));
    };

    // 스크립트 생성 메서드
    async function generateScript(url: string, duration: number) {
        isLoading.value = true;
        error.value = null;
        script.value = null;
        videoUrl.value = url;

        try {
            const response = await api.shorts.generateScript({ url, duration });

            if (response) {
                script.value = response;
            } else {
                error.value = '스크립트 생성에 실패했습니다.';
            }
        } catch (e) {
            error.value = e instanceof Error ? e.message : '예상치 못한 오류가 발생했습니다.';
        } finally {
            isLoading.value = false;
        }
    }

    // 총 영상 길이 계산
    const totalDuration = computed(() => {
        return script.value?.scene.reduce((acc, scene) => acc + scene.duration, 0) || 0;
    });

    return {
        isLoading,
        error,
        script,
        videoUrl,
        currentTime,
        duration,
        isPlaying,
        isMuted,
        playbackSpeed,
        totalDuration,
        setTime,
        setDuration,
        togglePlay,
        toggleMute,
        setPlaybackSpeed,
        seekRelative,
        generateScript
    };
}); 