"""
User-related Pydantic schemas
"""
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


class AddressBase(BaseModel):
    """Base address schema"""
    street: str
    city: str
    state: str
    country: str
    postal_code: str
    is_default: bool = False


class AddressCreate(AddressBase):
    """Address creation schema"""
    pass


class AddressUpdate(BaseModel):
    """Address update schema"""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    is_default: Optional[bool] = None


class AddressResponse(AddressBase):
    """Address response schema"""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    full_address: str

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema"""
    password: str


class UserUpdate(BaseModel):
    """User update schema"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(UserBase):
    """User response schema"""
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    full_name: str
    addresses: List[AddressResponse] = []

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    """User profile update schema"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str