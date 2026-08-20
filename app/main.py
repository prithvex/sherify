from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.v1.api import api_v1_router
from app.api.v1.endpoints.tracking import router as tracking_router
from app.core.config import settings
from app.schemas.health import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    yield
    # Shutdown actions


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Automated Mass Campaign Manager backend service.",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Set up CORS middleware
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Root Health Check",
    description="Check overall application and database connectivity status.",
)
async def root_health_check(db: AsyncSession = Depends(get_db)):
    db_status = "ok"
    app_status = "ok"
    http_status = status.HTTP_200_OK

    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"
        app_status = "degraded"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    content = {
        "status": app_status,
        "database": db_status,
        "version": "0.1.0",
        "app_name": settings.APP_NAME,
    }

    return JSONResponse(status_code=http_status, content=content)


# Mount public tracking pixel route at /track
app.include_router(tracking_router, prefix="/track", tags=["Tracking"])

# Include API v1 router
app.include_router(api_v1_router, prefix="/api/v1")
