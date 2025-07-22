from fastapi import APIRouter, Depends
from app.core.dependencies import get_services, Services
from app.models.schemas import Response


router = APIRouter(prefix="/crawling")


@router.get("/page-image")  # crawling/page-image
async def get_page_image(url: str, services: Services = Depends(get_services)):
    image_url = await services.crawling.crawl_website_image(url)
    return Response.with_data(image_url)


@router.get("/page-proxy-image")  # crawling/page-proxy-image
async def get_page_proxy_image(url: str, services: Services = Depends(get_services)):
    image_url = await services.crawling.crawl_website_with_proxy(url)
    return Response.with_data(image_url)


@router.get("/playwright/page")  # crawling/playwright/page
async def get_page_by_playwright(url: str, services: Services = Depends(get_services)):
    html_content = await services.crawling.crawl_website_with_playwright(url)
    return Response.with_data(html_content)
