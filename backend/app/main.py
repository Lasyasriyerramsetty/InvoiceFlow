from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import Response

from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.evaluation import router as evaluation_router
from backend.app.api.v1.invoices import router as invoices_router
from backend.app.core.config import get_settings
from backend.app.infrastructure.database.session import engine

logger = structlog.get_logger(__name__)
settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])

REQUEST_COUNT = Counter("ap_http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is managed by Alembic migrations (see ./migrations and pyproject
    # scripts: `alembic upgrade head`). We no longer use create_all in app.
    logger.info("application_started", env=settings.app_env)
    yield
    await engine.dispose()
    logger.info("application_shutdown")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Enterprise AI-powered Accounts Payable automation platform",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(invoices_router, prefix=settings.api_v1_prefix)
app.include_router(evaluation_router, prefix=settings.api_v1_prefix)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    response = await call_next(request)
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    return response


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name, "version": "1.0.0"}


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
