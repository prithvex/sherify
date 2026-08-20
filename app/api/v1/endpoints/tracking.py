from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.tracking_service import tracking_service

router = APIRouter()


@router.get(
    "/open/{tracking_token}",
    summary="Email open tracking pixel",
    responses={
        200: {
            "content": {"image/gif": {}},
            "description": "1x1 transparent tracking pixel GIF",
        }
    },
)
async def track_email_open(
    tracking_token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public tracking pixel endpoint. Records email open event idempotently and returns a 1x1 transparent GIF.
    """
    gif_bytes = await tracking_service.record_open(db=db, tracking_token=tracking_token)

    return Response(
        content=gif_bytes,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
