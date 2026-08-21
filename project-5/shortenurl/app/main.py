import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.repositories.database import init_db
from app.routers.url_router import router as url_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="分層架構 FastAPI 短網址服務：Routers (HTTP) / Services (邏輯) / Repositories (資料庫) / Pydantic (安檢)",
    lifespan=lifespan,
)

# Mount URL API and Redirection routes
app.include_router(url_router)

# Mount Static frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
async def serve_dashboard():
    index_path = os.path.join(static_dir, "index.html")
    return FileResponse(index_path)
