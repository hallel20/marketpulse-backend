"""
Cart and wishlist Pydantic schemas
"""
import uuid
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class CartItemBase(BaseModel):
    """Base cart item schema"""
    product_id: uuid.UUID
    quantity: int = Field(gt=0)
    variant_info: Optional[str] = None


class CartItemCreate(CartItemBase):
    """Cart item creation schema"""
    pass


class CartItemUpdate(BaseModel):
    """Cart item update schema"""
    quantity: int = Field(gt=0)
    variant_info: Optional[str] = None


class CartItemResponse(BaseModel):
    """Cart item response schema"""
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    variant_info: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Product information
    product_name: str
    product_slug: str
    product_price: Decimal
    product_image_url: Optional[str]
    product_stock: int
    is_available: bool
    
    # Calculated fields
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    """Cart response schema"""
    items: List[CartItemResponse]
    item_count: int
    subtotal: Decimal
    estimated_tax: Decimal
    estimated_shipping: Decimal
    estimated_total: Decimal


class WishlistItemResponse(BaseModel):
    """Wishlist item response schema"""
    id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime
    
    # Product information
    product_name: str
    product_slug: str
    product_price: Decimal
    product_image_url: Optional[str]
    product_stock: int
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class WishlistResponse(BaseModel):
    """Wishlist response schema"""
    items: List[WishlistItemResponse]
    item_count: int


class MoveToCartRequest(BaseModel):
    """Move wishlist item to cart request"""
    quantity: int = Field(default=1, gt=0)
    variant_info: Optional[str] = None