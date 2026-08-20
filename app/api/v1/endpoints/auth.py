from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth_service import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    register_in: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user with unique email and hashed password.
    """
    return await auth_service.register(db, register_in)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and obtain JWT token",
)
async def login(
    login_in: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with email and password to receive a JWT access token.
    """
    return await auth_service.authenticate(db, login_in)
