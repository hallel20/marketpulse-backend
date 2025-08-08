"""
Authentication service for user management and JWT tokens
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserCreate
from app.utils.exceptions import ValidationException

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_email_verification_token(self, email: str) -> str:
        """Create email verification token"""
        expire = datetime.utcnow() + timedelta(hours=24)
        to_encode = {"sub": email, "exp": expire, "type": "email_verification"}
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_password_reset_token(self, email: str) -> str:
        """Create password reset token"""
        expire = datetime.utcnow() + timedelta(hours=1)
        to_encode = {"sub": email, "exp": expire, "type": "password_reset"}
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str) -> Optional[dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                return None
            return payload
        except JWTError:
            return None
    
    def verify_access_token(self, token: str) -> Optional[dict]:
        """Verify access token"""
        return self.verify_token(token, "access")
    
    def verify_refresh_token(self, token: str) -> Optional[dict]:
        """Verify refresh token"""
        return self.verify_token(token, "refresh")
    
    def verify_email_verification_token(self, token: str) -> Optional[str]:
        """Verify email verification token"""
        payload = self.verify_token(token, "email_verification")
        if payload:
            return payload.get("sub")
        return None
    
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verify password reset token"""
        payload = self.verify_token(token, "password_reset")
        if payload:
            return payload.get("sub")
        return None
    
    async def get_user_by_email(self, email: str, session: AsyncSession) -> Optional[User]:
        """Get user by email"""
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: uuid.UUID, session: AsyncSession) -> Optional[User]:
        """Get user by ID"""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def authenticate_user(
        self, 
        email: str, 
        password: str, 
        session: AsyncSession
    ) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await self.get_user_by_email(email, session)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    async def create_user(self, user_data: RegisterRequest, session: AsyncSession) -> User:
        """Create a new user"""
        # Validate password strength
        if len(user_data.password) < 8:
            raise ValidationException("Password must be at least 8 characters long")
        
        # Hash password
        hashed_password = self.get_password_hash(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        return user
    
    async def update_password(
        self, 
        user: User, 
        new_password: str, 
        session: AsyncSession
    ) -> None:
        """Update user password"""
        # Validate password strength
        if len(new_password) < 8:
            raise ValidationException("Password must be at least 8 characters long")
        
        # Hash new password
        user.password_hash = self.get_password_hash(new_password)
        await session.commit()
    
    async def get_current_user(self, token: str, session: AsyncSession) -> Optional[User]:
        """Get current user from JWT token"""
        payload = self.verify_access_token(token)
        if not payload:
            return None
        
        email: str = payload.get("sub")
        if not email:
            return None
        
        user = await self.get_user_by_email(email, session)
        return user