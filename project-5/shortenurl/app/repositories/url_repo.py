from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.repositories.database import URLModel, ClickModel

class URLRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_code(self, code: str) -> Optional[URLModel]:
        stmt = select(URLModel).where(URLModel.short_code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_target(self, target_url: str) -> Optional[URLModel]:
        stmt = select(URLModel).where(URLModel.target_url == target_url)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_clicks(self, code: str) -> Optional[URLModel]:
        stmt = select(URLModel).where(URLModel.short_code == code).options(selectinload(URLModel.click_logs))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 20) -> List[URLModel]:
        stmt = select(URLModel).order_by(URLModel.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, short_code: str, target_url: str) -> URLModel:
        url_obj = URLModel(short_code=short_code, target_url=target_url)
        self.db.add(url_obj)
        await self.db.commit()
        await self.db.refresh(url_obj)
        return url_obj

    async def record_click(self, url_id: int, ip: Optional[str], user_agent: Optional[str], referer: Optional[str]) -> None:
        # Increment click counter
        stmt = update(URLModel).where(URLModel.id == url_id).values(clicks=URLModel.clicks + 1)
        await self.db.execute(stmt)

        # Insert click log
        click_log = ClickModel(url_id=url_id, ip=ip, user_agent=user_agent, referer=referer)
        self.db.add(click_log)
        await self.db.commit()
