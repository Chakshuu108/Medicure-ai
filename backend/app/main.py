import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, clinical, schedule
from app.config import get_settings, is_groq_configured, reload_settings
from app.database import Base, engine
from app.services.proactive_scheduler import start_proactive_scheduler, stop_proactive_scheduler

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    reload_settings()  # pick up latest backend/.env on every server start
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")
    start_proactive_scheduler()
    yield
    await stop_proactive_scheduler()
    await engine.dispose()


app = FastAPI(
    title="MediCure AI Platform",
    description="Agentic AI Healthcare Platform with LangGraph multi-agent orchestration",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(clinical.router)
app.include_router(admin.router)
app.include_router(schedule.router)


@app.get("/health")
async def health():
    from app.config import get_settings
    s = get_settings()
    return {
        "status": "ok",
        "service": "medicure-api",
        "version": "3.0.0",
        "groq_configured": is_groq_configured(),
        "guardian_proactive_enabled": s.guardian_proactive_enabled,
        "guardian_scan_interval_hours": s.guardian_scan_interval_hours,
    }
