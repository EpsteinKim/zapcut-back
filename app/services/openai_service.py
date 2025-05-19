from openai import OpenAI
from app.core.config import get_settings

class OpenAIService:
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    async def generate_chat_response(self, prompt: str) -> str:
        response = self.client.responses.create(
            model="o4-mini",
            input=prompt
        )
        return response.output_text
    
    async def generate_shorts_content(self, topic: str, style: str, duration: str) -> dict:
        system_prompt = f"""You are a professional YouTube Shorts content creator.
        Create engaging content for a {duration} video in a {style} style.
        Focus on creating viral-worthy content that will engage viewers."""

        user_prompt = f"""Create a YouTube Shorts video about: {topic}
        Include:
        1. An attention-grabbing title
        2. A compelling description
        3. Relevant hashtags (5-7)
        4. A detailed script for the {duration} video
        Make it engaging and optimized for YouTube Shorts format."""

        response = self.client.responses.create(
            model="o4-mini",
            input=user_prompt
        )
        
        content = response.output_text
        lines = content.split('\n')
        
        return {
            "title": lines[0].replace('Title:', '').strip(),
            "description": lines[1].replace('Description:', '').strip(),
            "hashtags": [tag.strip() for tag in lines[2].replace('Hashtags:', '').split('#') if tag.strip()],
            "script": '\n'.join(lines[3:]).replace('Script:', '').strip()
        } 