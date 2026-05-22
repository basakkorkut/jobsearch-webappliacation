import certifi
import logging
import os

# macOS SSL fix — must be before any network imports
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.chat import router as chat_router

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify LM Studio is reachable
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.lm_studio_url}/v1/models")
            models = resp.json()
            model_ids = [m.get("id", "") for m in models.get("data", [])]
            logger.info("LM Studio bağlandı. Yüklü modeller: %s", model_ids)
    except Exception as e:
        logger.warning("LM Studio şu an erişilemiyor (%s) — servis yine de başlıyor", e)

    yield

    logger.info("AI Agent Service kapatılıyor")


app = FastAPI(
    title="AI Agent Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
async def health():
    lm_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{settings.lm_studio_url}/v1/models")
            lm_status = "up" if resp.status_code == 200 else "error"
    except Exception:
        lm_status = "down"

    return {
        "status": "ok",
        "services": {
            "lm_studio": lm_status,
        },
    }
