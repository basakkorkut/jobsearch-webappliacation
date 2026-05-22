"""
API Gateway — path-based reverse proxy.

Routing table (first match wins):
  /api/v1/agent/*        → ai-agent-service :8003
  /api/v1/*              → job-service       :8001
  /health                → aggregate all services
"""
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.core.config import settings

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

# Ordered routing table — (path_prefix, upstream_base_url)
ROUTES: list[tuple[str, str]] = [
    ("/api/v1/agent",  settings.ai_agent_service_url),
    ("/api/v1",        settings.job_service_url),
]

# Shared async HTTP client (connection-pooled)
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    if _client is None:
        raise RuntimeError("HTTP client not initialised")
    return _client


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    # Agent servis local LLM çağrısı 30sn+ sürebilir
    _client = httpx.AsyncClient(
        timeout=httpx.Timeout(connect=5, read=120, write=10, pool=5),
        follow_redirects=True,
    )
    logger.info("API Gateway başlatıldı")
    logger.info("  job-service      → %s", settings.job_service_url)
    logger.info("  ai-agent-service → %s", settings.ai_agent_service_url)
    yield
    await _client.aclose()
    logger.info("API Gateway kapatıldı")


app = FastAPI(title="API Gateway", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health (aggregate) ────────────────────────────────────────────────────────

@app.get("/health", tags=["gateway"])
async def health():
    checks = {
        "job_service":       settings.job_service_url,
        "ai_agent_service":  settings.ai_agent_service_url,
    }
    results: dict[str, str] = {}
    client = _get_client()
    for name, base in checks.items():
        try:
            r = await client.get(f"{base}/health", timeout=3)
            results[name] = "up" if r.status_code == 200 else "error"
        except Exception:
            results[name] = "down"

    overall = "ok" if all(v == "up" for v in results.values()) else "degraded"
    return {"status": overall, "services": results}


# ── Proxy ─────────────────────────────────────────────────────────────────────

def _resolve_upstream(path: str) -> str | None:
    """Return upstream base URL for the given request path."""
    for prefix, upstream in ROUTES:
        if path.startswith(prefix):
            return upstream
    return None


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    tags=["proxy"],
    include_in_schema=False,
)
async def proxy(request: Request, path: str):
    full_path = f"/{path}"
    upstream = _resolve_upstream(full_path)

    if upstream is None:
        return Response(
            content=b'{"detail":"route not found"}',
            status_code=404,
            media_type="application/json",
        )

    # Build target URL with query string
    target_url = f"{upstream}{full_path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    # Forward headers — drop hop-by-hop headers
    HOP_BY_HOP = {"host", "content-length", "transfer-encoding", "connection",
                  "keep-alive", "proxy-authenticate", "proxy-authorization",
                  "te", "trailers", "upgrade"}
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in HOP_BY_HOP
    }

    body = await request.body()

    logger.debug("→ %s %s", request.method, target_url)

    try:
        upstream_resp = await _get_client().request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )
    except httpx.ConnectError:
        return Response(
            content=b'{"detail":"upstream service unavailable"}',
            status_code=503,
            media_type="application/json",
        )
    except httpx.TimeoutException:
        return Response(
            content=b'{"detail":"upstream service timed out"}',
            status_code=504,
            media_type="application/json",
        )

    # Strip hop-by-hop from response headers too
    resp_headers = {
        k: v for k, v in upstream_resp.headers.items()
        if k.lower() not in HOP_BY_HOP
    }

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=resp_headers,
        media_type=upstream_resp.headers.get("content-type"),
    )
