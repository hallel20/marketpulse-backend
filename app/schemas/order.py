"""
Order-related Pydantic schemas
"""
import uuid
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus, PaymentStatus


class OrderItemBase(BaseModel):
    """Base order item schema"""
    product_id: uuid.UUID
    quantity: int = Field(gt=0)
    variant_info: Optional[str] = None


class OrderItemCreate(OrderItemBase):
    """Order item creation schema"""
    pass


class OrderItemResponse(OrderItemBase):
    """Order item response schema"""
    id: uuid.UUID
    unit_price: Decimal
    total_price: Decimal
    product_name: str
    product_sku: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    """Base order schema"""
    shipping_address: str
    billing_address: str
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    """Order creation schema"""
    items: List[OrderItemCreate]
    payment_method: str = "stripe"


class OrderUpdate(BaseModel):
    """Order update schema"""
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(OrderBase):
    """Order response schema"""
    id: uuid.UUID
    order_number: str
    user_id: uuid.UUID
    status: OrderStatus
    payment_status: PaymentStatus
    subtotal: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    currency: str
    tracking_number: Optional[str]
    carrier: Optional[str]
    payment_intent_id: Optional[str]
    payment_method: Optional[str]
    created_at: datetime
    updated_at: datetime
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    item_count: int
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    """Order list response schema"""
    id: uuid.UUID
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    total_amount: Decimal
    currency: str
    item_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    """Order status update schema"""
    status: OrderStatus
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    notes: Optional[str] = None


class OrderSearchQuery(BaseModel):
    """Order search query schema"""
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class OrderSearchResponse(BaseModel):
    """Order search response schema"""
    orders: List[OrderListResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int