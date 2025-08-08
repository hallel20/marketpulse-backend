"""
Authentication API routes
"""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_async_session
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    Token,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.utils.exceptions import ValidationException, UnauthorizedException
from app.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter()
security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: RegisterRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Register a new user account
    
    - **email**: Valid email address
    - **password**: Strong password (min 8 characters)
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **phone**: Optional phone number
    """
    auth_service = AuthService()
    
    # Check if user already exists
    existing_user = await auth_service.get_user_by_email(user_data.email, session)
    if existing_user:
        raise ValidationException("Email address is already registered")
    
    # Create new user
    user = await auth_service.create_user(user_data, session)
    
    # Send verification email
    email_service = EmailService()
    verification_token = auth_service.create_email_verification_token(user.email)
    background_tasks.add_task(
        email_service.send_verification_email,
        user.email,
        user.first_name,
        verification_token
    )
    
    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Authenticate user and return JWT tokens
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns access token and refresh token
    """
    auth_service = AuthService()
    
    # Authenticate user
    user = await auth_service.authenticate_user(
        credentials.email,
        credentials.password,
        session
    )
    
    if not user:
        raise UnauthorizedException("Invalid email or password")
    
    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")
    
    # Update last login
    user.last_login = datetime.utcnow()
    await session.commit()
    
    # Create tokens
    access_token = auth_service.create_access_token({"sub": user.email, "user_id": str(user.id)})
    refresh_token = auth_service.create_refresh_token({"sub": user.email, "user_id": str(user.id)})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    token_data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token and refresh token
    """
    auth_service = AuthService()
    
    # Verify refresh token
    payload = auth_service.verify_refresh_token(token_data.refresh_token)
    if not payload:
        raise UnauthorizedException("Invalid refresh token")
    
    # Get user
    user = await auth_service.get_user_by_email(payload.get("sub"), session) # type: ignore
    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")
    
    # Create new tokens
    token = {"sub": user.email, "user_id": str(user.id)}
    access_token = auth_service.create_access_token(token)
    new_refresh_token = auth_service.create_refresh_token(token)
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout current user (client should delete tokens)
    """
    # In a production environment, you might want to blacklist the token
    # For now, we rely on the client to delete the tokens
    return {"message": "Successfully logged out"}


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    request_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Request password reset
    
    - **email**: User's email address
    
    Sends password reset email if user exists
    """
    auth_service = AuthService()
    user = await auth_service.get_user_by_email(request_data.email, session)
    
    if user and user.is_active:
        # Create password reset token
        reset_token = auth_service.create_password_reset_token(user.email)
        
        # Send reset email
        email_service = EmailService()
        background_tasks.add_task(
            email_service.send_password_reset_email,
            user.email,
            user.first_name,
            reset_token
        )
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    request_data: PasswordResetConfirm,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Reset password using reset token
    
    - **token**: Password reset token from email
    - **new_password**: New password
    """
    auth_service = AuthService()
    
    # Verify reset token
    email = auth_service.verify_password_reset_token(request_data.token)
    if not email:
        raise UnauthorizedException("Invalid or expired reset token")
    
    # Get user and update password
    user = await auth_service.get_user_by_email(email, session)
    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")
    
    # Update password
    await auth_service.update_password(user, request_data.new_password, session)
    
    return {"message": "Password successfully reset"}


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def verify_email(
    request: Request,
    token: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Verify email address using verification token
    
    - **token**: Email verification token from email
    """
    auth_service = AuthService()
    
    # Verify email token
    email = auth_service.verify_email_verification_token(token)
    if not email:
        raise UnauthorizedException("Invalid or expired verification token")
    
    # Get user and mark as verified
    user = await auth_service.get_user_by_email(email, session)
    if not user:
        raise UnauthorizedException("User not found")
    
    # Update verification status
    user.is_verified = True
    await session.commit()
    
    return {"message": "Email successfully verified"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's profile information
    """
    return current_user