from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response
from app.models.schemas import SceneRequest, ShortsContentRequest, ShortsResponse, UrlRequest
from app.services import web_scraper, openai_service
from app.exceptions.http_exceptions import ServerException
from app.core.dependencies import get_services, Services
import os

router = APIRouter()


@router.post("/test")
async def test(request: ShortsContentRequest, openai_service=Depends(openai_service.OpenAIService)):
    async with web_scraper.AsyncWebScraper() as scraper:
        result = await scraper.scrape_single_page(request.url)
    video_script = await openai_service.generate_shorts_content(result["content"], f"{request.duration}s")
    # 과정 1 종료 (영상 컨텐츠 스크립트 생성)\
    translated_description = await openai_service.translate_to_english(
        "스마트폰으로 병원 예약 화면을 터치하는 손 클로즈업, 화면에 '예약하기' 버튼 강조"
    )

    image_url = await openai_service.generate_shorts_image(translated_description)
    return image_url


@router.post("/test2")
async def create_sample_video(
    services: Services = Depends(get_services),
):
    try:
        # 샘플 장면 생성
        scenes = [
            SceneRequest(
                captions=["안녕하세요!", "샘플 비디오입니다."],
                video_url="app/sample_video/sample1.mp4",
            ),
            SceneRequest(
                captions=["두 번째 장면입니다.", "배경 음악과 함께"],
                video_url="app/sample_video/sample2.mp4",
            ),
            SceneRequest(
                captions=["세 번째 장면입니다.", "마지막 장면아니죠"],
                video_url="app/sample_video/sample3.mp4",
            ),
            SceneRequest(
                captions=[
                    "네 번째 장면입니다.",
                    "이번엔 조금 길었으면 좋겠네요",
                    "자막 테스트입니다." "마지막 장면입니다.",
                ],
                video_url="app/sample_video/sample4.mp4",
            ),
        ]

        # 비디오 생성
        video = await services.test_video.create_video(
            scenes=scenes,
            background_music_path="sample_audio/Out of Flux - CHONKLAP.mp3",
            music_volume=0.3,
            tts_volume=0.5,
        )

        # output 디렉토리 확인 및 생성
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 비디오 저장
        output_path = "output/sample_output2.mp4"
        services.test_video.save_video(video, output_path)

        return {"message": "비디오가 성공적으로 생성되었습니다.", "output_path": output_path}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise ServerException(str(e))
