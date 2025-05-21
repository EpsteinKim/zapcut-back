from openai import OpenAI
from app.core.config import get_settings
from app.exceptions.http_exceptions import UnprocessableEntityError


class OpenAIService:
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    async def generate_chat_response(self, prompt: str) -> str:
        system_prompt = f"""
        Based on the user's prompt, first extract the relevant information from the product description. 
        Then, using that extracted data, generate the following:
        1. A catchy title suitable for a YouTube Shorts video.
        2. 3 short caption lines for the video (each lasting about 3–6 seconds).
        3. A scene idea that matches each caption (describe what should appear visually).
        4. Up to 5 relevant hashtags.
        5. Write caption without emojis
        6. 한국어로 작성해주세요.
        Please format the result clearly and neatly.
        """
        response = self.client.responses.create(
            model="o4-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.output_text
    
    async def generate_shorts_content(self, content: str, duration: str) -> str:
        if (len(content) < 100):
            raise UnprocessableEntityError("정보가 너무 적거나, 접근할 수 없는 페이지입니다.", {"content": content})
        system_prompt = f"""You are a professional YouTube Shorts content creator and video script writer.
        Your task is to create engaging content for a {duration} YouTube Shorts video.
        You should create content that is optimized for short-form video format and can be visualized using Stable Diffusion.
        Focus on creating viral-worthy content that will engage viewers.
        Please write all content in Korean.
        """

        user_prompt = f"""Create a YouTube Shorts video script based on the following content:
        
        {content}

        Please provide the following in a structured format:
        {{
            "title": "영상을 대표하는 매력적인 제목"
            "scene": [
                {{
                    "time": "0-2초",
                    "caption": ["첫 2초 동안 보여지며 진행될 음성 및 자막", ...]
                    "description": "Stable Diffusion으로 생성할 이미지에 대한 상세 설명"
                }},
                {{
                    "time": "장면에 맞는 초 분배",
                    "caption": ["다음 상황에 맞게 보여지며 진행될 텍스트와 음성자막", ...],
                    "description": "Stable Diffusion으로 생성할 이미지에 대한 상세 설명"
                }},
                ... (이런 형식으로 {duration} 동안 계속)
            ]
        
        }}
        
        각 시간대별로:
        - 캡션은 소개해주는 것처럼 작성
        - 이미지_설명은 Stable Diffusion이 이해할 수 있도록 구체적으로 작성
        - 전체적인 스토리 흐름이 자연스럽게 이어지도록 구성
        - 첫번째 장면을 제외하고 caption은 2개 이상
        - 화면 전환은 최대한 스피드하게 하면 좋음
        - 친근하게 설명하도록 작성
        """

        response = self.client.responses.create(
            model="o4-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        print(response.output_text)
        return response.output_text