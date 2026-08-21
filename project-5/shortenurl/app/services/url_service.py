import random
import string
from typing import Optional, List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.url_repo import URLRepository
from app.repositories.database import AsyncSessionLocal
from app.schemas.url import URLCreate, URLResponse, URLStatsResponse, ClickEvent
from app.core.config import settings

class URLService:
    def __init__(self, db: AsyncSession):
        self.repo = URLRepository(db)

    def _generate_code(self, length: int = 6) -> str:
        chars = string.ascii_letters + string.digits
        return "".join(random.choices(chars, k=length))

    async def shorten_url(self, data: URLCreate) -> URLResponse:
        # Check custom code availability
        if data.custom_code:
            existing = await self.repo.get_by_code(data.custom_code)
            if existing:
                raise HTTPException(status_code=409, detail=f"自訂短代碼 '{data.custom_code}' 已被使用")
            code = data.custom_code
        else:
            # Check if target URL already shortened
            existing = await self.repo.get_by_target(data.target_url)
            if existing:
                return self._to_response(existing)

            # Generate unique code with retry
            for _ in range(5):
                code = self._generate_code(settings.SHORT_CODE_LENGTH)
                if not await self.repo.get_by_code(code):
                    break
            else:
                raise HTTPException(status_code=500, detail="生成唯一短代碼失敗，請稍後重試")

        url_obj = await self.repo.create(short_code=code, target_url=data.target_url)
        return self._to_response(url_obj)

    async def get_target_url(self, code: str) -> tuple[int, str]:
        url_obj = await self.repo.get_by_code(code)
        if not url_obj:
            raise HTTPException(status_code=404, detail="找不到該短網址或已失效")
        return url_obj.id, url_obj.target_url

    async def get_stats(self, code: str) -> URLStatsResponse:
        url_obj = await self.repo.get_with_clicks(code)
        if not url_obj:
            raise HTTPException(status_code=404, detail="找不到該短網址統計資訊")

        clicks = [
            ClickEvent(
                timestamp=c.timestamp,
                ip=c.ip,
                user_agent=c.user_agent,
                referer=c.referer,
            )
            for c in sorted(url_obj.click_logs, key=lambda x: x.timestamp, reverse=True)[:50]
        ]

        return URLStatsResponse(
            short_code=url_obj.short_code,
            target_url=url_obj.target_url,
            total_clicks=url_obj.clicks,
            created_at=url_obj.created_at,
            recent_clicks=clicks,
        )

    async def list_recent(self) -> List[URLResponse]:
        urls = await self.repo.list_recent()
        return [self._to_response(u) for u in urls]

    def _to_response(self, url_obj) -> URLResponse:
        return URLResponse(
            short_code=url_obj.short_code,
            short_url=f"{settings.BASE_URL}/{url_obj.short_code}",
            target_url=url_obj.target_url,
            clicks=url_obj.clicks,
            created_at=url_obj.created_at,
        )

# Independent Background Task runner with its own async session
async def record_click_background(url_id: int, ip: Optional[str], user_agent: Optional[str], referer: Optional[str]):
    async with AsyncSessionLocal() as session:
        repo = URLRepository(session)
        await repo.record_click(url_id=url_id, ip=ip, user_agent=user_agent, referer=referer)
