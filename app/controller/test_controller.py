from fastapi import APIRouter
from app.utils.io_processor import IOProcessor
from app.utils.video.audio_processor import AudioProcessor
from app.services.openai_service import OpenAIService
from app.core.service_locator import get_openai_service
from fastapi import Depends
from app.core.dependencies import get_current_user, get_services, Services

router = APIRouter(dependencies=[Depends(get_current_user)])

io_processor = IOProcessor()
audio_processor = AudioProcessor()


@router.get("/test")
async def test(services: Services = Depends(get_services)):
    test_obj = [
        "안녕! 오늘은 게이머들의 로망, 하이퍼엑스 클라우드 스팅어2 무선 게이밍 헤드셋을 파헤쳐 볼 거야!",
        "무선이라 선 꼬일 걱정 없이 자유롭게 움직일 수 있고, 2.4GHz 연결로 끊김 없이 쾌적한 게이밍 환경을 제공한다구!",
        "부드러운 이어컵과 가벼운 무게는 장시간 사용에도 굿! 답답함 없이 게임을 즐길 수 있다는게 최고 장점이지.",
        "팀 보이스도 선명하게 들리고, 몰입감 넘치는 사운드는 게임의 재미를 한층 더 끌어올려 줄거야.",
        "쿠팡에서 로켓배송으로 빠르게 받아보고, 지금 바로 게임 속으로 풍덩 빠져보자!",
    ]
    return await audio_processor.get_audio_subclip(
        "https://cdn.zapcut.io/expired/no_61372317291485731753409953669.mp3", test_obj
    )
    return await services.google_ai.get_transcription(
        "https://cdn.zapcut.io/expired/no_61372317291485731753409953669.mp3", test_obj
    )
