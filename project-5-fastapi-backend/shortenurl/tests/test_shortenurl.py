import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.repositories.database import init_db, engine, Base

@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_short_url():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/shorten",
            json={"target_url": "https://cursor.com/features/agent"},
        )
        assert res.status_code == 201
        data = res.json()
        assert "short_code" in data
        assert data["target_url"] == "https://cursor.com/features/agent"
        assert data["clicks"] == 0

@pytest.mark.asyncio
async def test_custom_code_and_conflict():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/shorten",
            json={"target_url": "https://fastapi.tiangolo.com", "custom_code": "fastapi-docs"},
        )
        assert res.status_code == 201
        assert res.json()["short_code"] == "fastapi-docs"

        # Duplicate custom code should be 409
        res_dup = await client.post(
            "/api/v1/shorten",
            json={"target_url": "https://another.com", "custom_code": "fastapi-docs"},
        )
        assert res_dup.status_code == 409

@pytest.mark.asyncio
async def test_pydantic_validation_error():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Missing http/https protocol
        res = await client.post(
            "/api/v1/shorten",
            json={"target_url": "ftp://bad-url.com"},
        )
        assert res.status_code == 422

@pytest.mark.asyncio
async def test_redirect_and_background_task():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create short url
        create_res = await client.post(
            "/api/v1/shorten",
            json={"target_url": "https://news.ycombinator.com", "custom_code": "hn-news"},
        )
        assert create_res.status_code == 201

        # 2. Redirect
        redirect_res = await client.get("/hn-news", follow_redirects=False)
        assert redirect_res.status_code == 307
        assert redirect_res.headers["location"] == "https://news.ycombinator.com"

        # 3. Check stats
        stats_res = await client.get("/api/v1/urls/hn-news/stats")
        assert stats_res.status_code == 200
        stats_data = stats_res.json()
        assert stats_data["total_clicks"] >= 1
