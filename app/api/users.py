"""
User management API routes
"""
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.database import get_async_session
from app.dependencies import get_current_active_user
from app.models.user import User, Address
from app.schemas.user import (
    UserResponse,
    UserProfileUpdate,
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    PasswordChangeRequest
)
from app.services.auth_service import AuthService
from app.utils.exceptions import NotFoundException, ValidationException

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's complete profile with addresses
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update current user's profile information
    
    - **first_name**: Updated first name
    - **last_name**: Updated last name  
    - **phone**: Updated phone number
    """
    # Update user fields
    for field, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    await session.commit()
    await session.refresh(current_user)
    
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Change user's password
    
    - **current_password**: Current password for verification
    - **new_password**: New password
    """
    auth_service = AuthService()
    
    # Verify current password
    if not auth_service.verify_password(password_data.current_password, current_user.password_hash):
        raise ValidationException("Current password is incorrect")
    
    # Update password
    await auth_service.update_password(current_user, password_data.new_password, session)
    
    return {"message": "Password successfully changed"}


# Address Management
@router.get("/addresses", response_model=List[AddressResponse])
async def get_my_addresses(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all addresses for the current user
    """
    result = await session.execute(
        select(Address)
        .where(Address.user_id == current_user.id)
        .order_by(Address.is_default.desc(), Address.created_at.desc())
    )
    addresses = result.scalars().all()
    return addresses


@router.post("/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    address_data: AddressCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new address for the current user
    
    - **street**: Street address
    - **city**: City name
    - **state**: State/province
    - **country**: Country name
    - **postal_code**: Postal/ZIP code
    - **is_default**: Set as default address
    """
    # If this is set as default, unset other default addresses
    if address_data.is_default:
        await session.execute(
            select(Address)
            .where(Address.user_id == current_user.id)
            .where(Address.is_default == True)
        )
        existing_defaults = (await session.execute(
            select(Address).where(Address.user_id == current_user.id, Address.is_default == True)
        )).scalars().all()
        
        for addr in existing_defaults:
            addr.is_default = False
    
    # Create new address
    new_address = Address(
        user_id=current_user.id,
        **address_data.model_dump()
    )
    
    session.add(new_address)
    await session.commit()
    await session.refresh(new_address)
    
    return new_address


@router.get("/addresses/{address_id}", response_model=AddressResponse)
async def get_address(
    address_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get a specific address by ID
    """
    result = await session.execute(
        select(Address)
        .where(Address.id == address_id)
        .where(Address.user_id == current_user.id)
    )
    address = result.scalar_one_or_none()
    
    if not address:
        raise NotFoundException("Address not found")
    
    return address


@router.put("/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: uuid.UUID,
    address_data: AddressUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update a specific address
    """
    # Get address
    result = await session.execute(
        select(Address)
        .where(Address.id == address_id)
        .where(Address.user_id == current_user.id)
    )
    address = result.scalar_one_or_none()
    
    if not address:
        raise NotFoundException("Address not found")
    
    # If setting as default, unset other defaults
    update_data = address_data.model_dump(exclude_unset=True)
    if update_data.get("is_default"):
        await session.execute(
            select(Address)
            .where(Address.user_id == current_user.id)
            .where(Address.is_default == True)
            .where(Address.id != address_id)
        )
        existing_defaults = (await session.execute(
            select(Address)
            .where(Address.user_id == current_user.id)
            .where(Address.is_default == True)
            .where(Address.id != address_id)
        )).scalars().all()
        
        for addr in existing_defaults:
            addr.is_default = False
    
    # Update address
    for field, value in update_data.items():
        setattr(address, field, value)
    
    await session.commit()
    await session.refresh(address)
    
    return address


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete a specific address
    """
    # Get address
    result = await session.execute(
        select(Address)
        .where(Address.id == address_id)
        .where(Address.user_id == current_user.id)
    )
    address = result.scalar_one_or_none()
    
    if not address:
        raise NotFoundException("Address not found")
    
    await session.delete(address)
    await session.commit()
    
    return {"message": "Address deleted successfully"}