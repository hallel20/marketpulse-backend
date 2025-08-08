"""
Pydantic schemas for MarketPulse Commerce API
"""
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    AddressCreate,
    AddressResponse,
    AddressUpdate
)
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ProductListResponse,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    ProductReviewCreate,
    ProductReviewResponse
)
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderItemResponse,
    OrderListResponse
)
from app.schemas.cart import (
    CartItemCreate,
    CartItemResponse,
    CartResponse,
    WishlistItemResponse,
    WishlistResponse
)
from app.schemas.auth import (
    Token,
    TokenData,
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest
)

__all__ = [
    # User schemas
    "UserCreate",
    "UserResponse", 
    "UserUpdate",
    "AddressCreate",
    "AddressResponse",
    "AddressUpdate",
    
    # Product schemas
    "ProductCreate",
    "ProductResponse",
    "ProductUpdate", 
    "ProductListResponse",
    "CategoryCreate",
    "CategoryResponse",
    "CategoryUpdate",
    "ProductReviewCreate",
    "ProductReviewResponse",
    
    # Order schemas
    "OrderCreate",
    "OrderResponse",
    "OrderItemResponse",
    "OrderListResponse",
    
    # Cart schemas
    "CartItemCreate",
    "CartItemResponse",
    "CartResponse",
    "WishlistItemResponse",
    "WishlistResponse",
    
    # Auth schemas
    "Token",
    "TokenData",
    "LoginRequest",
    "RegisterRequest", 
    "RefreshTokenRequest",
]