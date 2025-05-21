from fastapi import APIRouter, HTTPException
import tiktoken
from app.models.schemas import ChatResponse, TestRequest
from app.services.openai_service import OpenAIService
from app.services.web_scraper import AsyncWebScraper
import json

router = APIRouter()
openai_service = OpenAIService()
@router.post("/test", response_model=ChatResponse)
async def test(request: TestRequest):
    price_per_1k_gpt_4_1 = 0.002
    price_per_1k_o4_mini = 0.00015

    print(request.url)
    async with AsyncWebScraper() as scraper:
        result = await scraper.scrape_single_page(request.url)
    print(result['content'])
    content = await openai_service.generate_shorts_content(result['content'], "30s")

    # prompt = result['content']
    # gpt4_encoding = tiktoken.get_encoding('cl100k_base')
    # o4_mini_encoding = tiktoken.get_encoding('o200k_base')
    
    
    # gpt4_tokens = gpt4_encoding.encode(prompt)
    # o4_mini_tokens = o4_mini_encoding.encode(prompt)

    # gpt4_prompt_cost = (len(gpt4_tokens) / 1000) * price_per_1k_gpt_4_1
    # o4_mini_prompt_cost = (len(o4_mini_tokens) / 1000) * price_per_1k_o4_mini

    # print(gpt4_prompt_cost)
    # print(o4_mini_prompt_cost)

    return ChatResponse(message="Hello, World!", data='test')
