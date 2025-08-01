from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user, get_services, Services
from app.models.schemas import ApiResponse


router = APIRouter(prefix="/crawling", dependencies=[Depends(get_current_user)])


@router.get("/page")  # crawling/playwright/page
async def get_page_by_playwright(url: str, services: Services = Depends(get_services)):
    html_content = await services.crawling.crawl_website_with_playwright(url)
    return ApiResponse.with_data(html_content)
