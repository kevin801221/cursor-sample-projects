from typing import List
from fastapi import APIRouter, Depends, Request, BackgroundTasks, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.database import get_db
from app.services.url_service import URLService, record_click_background
from app.schemas.url import URLCreate, URLResponse, URLStatsResponse

router = APIRouter()

@router.post("/api/v1/shorten", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def create_short_url(data: URLCreate, db: AsyncSession = Depends(get_db)):
    service = URLService(db)
    return await service.shorten_url(data)

@router.get("/api/v1/urls", response_model=List[URLResponse])
async def list_recent_urls(db: AsyncSession = Depends(get_db)):
    service = URLService(db)
    return await service.list_recent()

@router.get("/api/v1/urls/{code}/stats", response_model=URLStatsResponse)
async def get_url_stats(code: str, db: AsyncSession = Depends(get_db)):
    service = URLService(db)
    return await service.get_stats(code)

@router.get("/{code}")
async def redirect_short_url(
    code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    service = URLService(db)
    url_id, target_url = await service.get_target_url(code)

    # Dispatch BackgroundTask without blocking redirection
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    referer = request.headers.get("referer")

    background_tasks.add_task(
        record_click_background,
        url_id=url_id,
        ip=client_ip,
        user_agent=user_agent,
        referer=referer,
    )

    return RedirectResponse(url=target_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
