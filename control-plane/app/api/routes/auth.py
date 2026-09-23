"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.database import get_db, DBUser
from app.core.security import JWTManager
from shared.schemas.requests import LoginRequest, RegisterRequest
from shared.schemas.responses import TokenResponse

router = APIRouter()


class UserResponse(BaseModel):
    """User response"""
    id: str
    email: str
    username: str
    roles: list


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """User login"""
    # Query user
    result = await db.execute(
        select(DBUser).where(DBUser.email == request.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not JWTManager.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create tokens
    access_token = JWTManager.create_access_token(
        user_id=user.id,
        email=user.email,
        roles=user.roles
    )
    
    refresh_token = JWTManager.create_refresh_token(
        user_id=user.id,
        email=user.email
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """User registration"""
    # Check if email exists
    result = await db.execute(
        select(DBUser).where(DBUser.email == request.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username exists
    result = await db.execute(
        select(DBUser).where(DBUser.username == request.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user
    user = DBUser(
        email=request.email,
        username=request.username,
        password_hash=JWTManager.get_password_hash(request.password),
        roles=["user"],
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        roles=user.roles
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token"""
    payload = JWTManager.decode_token(refresh_token)
    
    if not payload or payload.dict().get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    result = await db.execute(
        select(DBUser).where(DBUser.id == payload.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    access_token = JWTManager.create_access_token(
        user_id=user.id,
        email=user.email,
        roles=user.roles
    )
    
    new_refresh_token = JWTManager.create_refresh_token(
        user_id=user.id,
        email=user.email
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token
    )
