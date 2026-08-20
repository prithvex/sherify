from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repo import user_repository
from app.schemas.user import TokenResponse, UserLogin, UserRegister


class AuthService:
    async def register(self, db: AsyncSession, register_in: UserRegister) -> User:
        # Check if email is already registered
        existing_user = await user_repository.get_by_email(db, register_in.email.strip().lower())
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

        hashed_password = get_password_hash(register_in.password)
        user = User(
            email=register_in.email.strip().lower(),
            password_hash=hashed_password,
            is_active=True,
        )
        return await user_repository.create(db, user)

    async def authenticate(self, db: AsyncSession, login_in: UserLogin) -> TokenResponse:
        user = await user_repository.get_by_email(db, login_in.email.strip().lower())
        if not user or not verify_password(login_in.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token(data={"sub": str(user.id), "email": user.email})
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


auth_service = AuthService()
