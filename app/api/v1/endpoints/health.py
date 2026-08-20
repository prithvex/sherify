from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="V1 Health Check",
    description="Check application and database connectivity status.",
)
async def v1_health_check(db: AsyncSession = Depends(get_db)):
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
