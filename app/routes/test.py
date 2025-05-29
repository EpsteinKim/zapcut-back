from fastapi import APIRouter, Depends, HTTPException, Response
from app.models.schemas import SceneRequest, ShortsContentRequest, ShortsResponse, UrlRequest
from app.services.openai_service import OpenAIService
from app.services.web_scraper import AsyncWebScraper
import json
from app.services.video_service import VideoService
from app.exceptions.http_exceptions import ServerException

router = APIRouter()
openai_service = OpenAIService()


@router.post("/test")
async def test(request: ShortsContentRequest):
    async with AsyncWebScraper() as scraper:
        result = await scraper.scrape_single_page(request.url)
    video_script = await openai_service.generate_shorts_scripts(result["content"], f"{request.duration}s")
    # 과정 1 종료 (영상 컨텐츠 스크립트 생성)
    video_script = {
        "title": "쉰 목소리, 그냥 넘기지 마세요! 후두암 체크리스트",
        "scene": [
            {
                "time": "0-2초",
                "caption": ["목소리 쉬면 혹시 '후두암'?"],
                "description": "젊은 남녀가 카메라를 향해 손으로 목을 가리키며 놀란 표정을 짓는 클로즈업, 밝은 색 배경에 큰 텍스트 오버레이",
            },
            {
                "time": "2-5초",
                "caption": [
                    "후두암은 목소리·호흡 기관에 생긴 암이에요",
                    "전체 암의 2~5%를 차지해요",
                ],
                "description": "해부학적 스타일의 후두(목소리 상자) 단면도, 투명한 인체 위에 후두 부위가 붉게 강조된 의학 일러스트",
            },
            {
                "time": "5-8초",
                "caption": [
                    "쉰 목소리, 목 이물감 느껴져요?",
                    "2주 이상 지속되면 검진이 필수!",
                ],
                "description": "마이크 앞에서 말을 하려다 목을 만지며 불편해하는 중년 여성, 말풍선 형태의 자막 박스",
            },
            {
                "time": "8-11초",
                "caption": [
                    "삼킬 때 통증 있어요?",
                    "기침·객혈·체중 감소까지 동반될 수 있어요",
                ],
                "description": "고통스러운 표정으로 물을 삼키는 남성, 물컵 근처에 피꽃 아이콘과 체중계 그림자",
            },
            {
                "time": "11-14초",
                "caption": [
                    "흡연·과음은 후두암 위험 UP🚨",
                    "HPV 바이러스 감염도 원인 중 하나",
                ],
                "description": "담배와 술병이 뿌옇게 연기로 뒤덮인 이미지, 바이러스 입자 모형이 함께 배치된 콜라주",
            },
            {
                "time": "14-17초",
                "caption": [
                    "후두경 검사로 목 안을 직접 관찰",
                    "이상 있으면 조직검사로 확진!",
                ],
                "description": "의사가 내시경을 사용해 환자의 목 안을 보는 장면, 의료 장비가 선명하게 묘사된 클리닉 환경",
            },
            {
                "time": "17-20초",
                "caption": [
                    "초기엔 레이저 절제·방사선 치료",
                    "진행되면 수술·항암치료 병행",
                ],
                "description": "레이저 빔이 목 부위를 스캔하는 듯한 그래픽과 방사선 심볼, 한쪽에는 수술 장면 일러스트",
            },
            {
                "time": "20-23초",
                "caption": [
                    "조기 발견이 가장 중요!",
                    "목소리 지키려면 지금 바로 검진!",
                ],
                "description": "밝은 병원 로비에서 미소 짓는 의사와 환자, 검사실 입구 표지판이 보이는 따뜻한 분위기",
            },
            {
                "time": "23-26초",
                "caption": [
                    "쉰 목소리가 2주 넘게 계속된다면?",
                    "망설이지 말고 병원으로 Go!",
                ],
                "description": "스마트폰으로 병원 예약 화면을 터치하는 손 클로즈업, 화면에 '예약하기' 버튼 강조",
            },
            {
                "time": "26-30초",
                "caption": [
                    "구독·좋아요 누르고 건강정보 더 받아보세요!",
                    "다음 영상에서 만나요 😊",
                ],
                "description": "유튜브 좋아요·구독 버튼 아이콘이 튀어나오는 듯한 애니메이션 스타일, 배경에 하트 이펙트",
            },
        ],
    }

    translated_description = await openai_service.translate_to_english(
        "스마트폰으로 병원 예약 화면을 터치하는 손 클로즈업, 화면에 '예약하기' 버튼 강조"
    )

    image_url = await openai_service.generate_shorts_image(translated_description)
    return image_url

    # image_url = await openai_service.generate_shorts_image(
    #     "Anatomical style of laryngeal (voice box) cross-sectional view, medical illustrations with red emphasis on the laryngeal area above the transparent human body"
    # )
    # return image_url

    # return ShortsResponse(**video_script)


@router.post("/create-sample-video")
async def create_sample_video(video_service: VideoService = Depends(VideoService)):
    try:
        # 샘플 장면 생성
        scenes = [
            SceneRequest(caption=["안녕하세요!", "샘플 비디오입니다."], video_url="../sample_video/sample1.mp4"),
            SceneRequest(caption=["두 번째 장면입니다.", "배경 음악과 함께"], video_url="../sample_video/sample2.mp4"),
            SceneRequest(
                caption=["세 번째 장면입니다.", "마지막 장면입니다."], video_url="../sample_video/sample3.mp4"
            ),
        ]

        # 비디오 생성
        video = video_service.create_video(
            scenes=scenes, background_music_path="../sample_audio/background.mp3", music_volume=0.3
        )

        # 비디오 저장
        output_path = "output/sample_output.mp4"
        video_service.save_video(video, output_path)

        return Response(output_path)
    except Exception as e:
        raise ServerException(status_code=500, detail=str(e))
