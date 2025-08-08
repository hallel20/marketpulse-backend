"""
Product-related Pydantic schemas
"""
import uuid
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    """Base category schema"""
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_active: bool = True
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    """Category creation schema"""
    pass


class CategoryUpdate(BaseModel):
    """Category update schema"""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class CategoryResponse(CategoryBase):
    """Category response schema"""
    id: uuid.UUID
    created_at: datetime
    children: List["CategoryResponse"] = []

    model_config = ConfigDict(from_attributes=True)


class ProductImageResponse(BaseModel):
    """Product image response schema"""
    id: uuid.UUID
    image_url: str
    alt_text: Optional[str] = None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class ProductVariantResponse(BaseModel):
    """Product variant response schema"""
    id: uuid.UUID
    name: str
    value: str
    sku_suffix: Optional[str] = None
    price_adjustment: Decimal
    stock_quantity: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    """Base product schema"""
    name: str
    slug: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    category_id: uuid.UUID
    price: Decimal = Field(gt=0, decimal_places=2)
    cost_price: Optional[Decimal] = Field(None, decimal_places=2)
    sku: str
    stock_quantity: int = Field(ge=0)
    weight: Optional[Decimal] = Field(None, decimal_places=2)
    dimensions: Optional[str] = None
    is_active: bool = True
    is_featured: bool = False
    is_digital: bool = False
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ProductCreate(ProductBase):
    """Product creation schema"""
    pass


class ProductUpdate(BaseModel):
    """Product update schema"""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    cost_price: Optional[Decimal] = Field(None, decimal_places=2)
    sku: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    weight: Optional[Decimal] = Field(None, decimal_places=2)
    dimensions: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_digital: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ProductResponse(ProductBase):
    """Product response schema"""
    id: uuid.UUID
    view_count: int
    rating_average: Decimal
    rating_count: int
    created_at: datetime
    updated_at: datetime
    is_in_stock: bool
    main_image_url: Optional[str]
    category: CategoryResponse
    images: List[ProductImageResponse] = []
    variants: List[ProductVariantResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Product list response schema"""
    id: uuid.UUID
    name: str
    slug: str
    short_description: Optional[str]
    price: Decimal
    sku: str
    stock_quantity: int
    is_featured: bool
    rating_average: Decimal
    rating_count: int
    is_in_stock: bool
    main_image_url: Optional[str]
    category_name: str

    model_config = ConfigDict(from_attributes=True)


class ProductReviewBase(BaseModel):
    """Base product review schema"""
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = None
    comment: Optional[str] = None


class ProductReviewCreate(ProductReviewBase):
    """Product review creation schema"""
    product_id: uuid.UUID


class ProductReviewResponse(ProductReviewBase):
    """Product review response schema"""
    id: uuid.UUID
    product_id: uuid.UUID
    user_id: uuid.UUID
    is_verified_purchase: bool
    is_approved: bool
    created_at: datetime
    user_name: str

    model_config = ConfigDict(from_attributes=True)


class ProductSearchQuery(BaseModel):
    """Product search query schema"""
    q: str = ""
    category_id: Optional[uuid.UUID] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    in_stock_only: bool = False
    featured_only: bool = False
    sort_by: str = "relevance"  # relevance, price_asc, price_desc, rating, newest
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class ProductSearchResponse(BaseModel):
    """Product search response schema"""
    products: List[ProductListResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    facets: dict = {}