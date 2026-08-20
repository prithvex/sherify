from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    """
    Return the profile data for the authenticated user.
    """
    return current_user
