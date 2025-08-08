"""
Product-related database models
"""
import uuid
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    """Product category model"""
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(String(255))
    
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id")
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children"
    )
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"


class Product(Base):
    """Product model"""
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    short_description: Mapped[Optional[str]] = mapped_column(String(500))
    
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=False
    )
    
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cost_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    dimensions: Mapped[Optional[str]] = mapped_column(String(100))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_digital: Mapped[bool] = mapped_column(Boolean, default=False)
    
    meta_title: Mapped[Optional[str]] = mapped_column(String(255))
    meta_description: Mapped[Optional[str]] = mapped_column(String(500))
    
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    rating_average: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    images: Mapped[List["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    variants: Mapped[List["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    reviews: Mapped[List["ProductReview"]] = relationship(
        "ProductReview",
        back_populates="product"
    )
    cart_items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="product"
    )
    wishlist_items: Mapped[List["WishlistItem"]] = relationship(
        "WishlistItem",
        back_populates="product"
    )
    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="product"
    )

    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock"""
        return self.stock_quantity > 0

    @property
    def main_image_url(self) -> Optional[str]:
        """Get main product image URL"""
        if self.images:
            return next((img.image_url for img in self.images if img.sort_order == 0), None)
        return None

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}')>"


class ProductImage(Base):
    """Product image model"""
    __tablename__ = "product_images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False
    )
    
    image_url: Mapped[str] = mapped_column(String(255), nullable=False)
    alt_text: Mapped[Optional[str]] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="images")

    def __repr__(self) -> str:
        return f"<ProductImage(id={self.id}, product_id={self.product_id})>"


class ProductVariant(Base):
    """Product variant model (size, color, etc.)"""
    __tablename__ = "product_variants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Size", "Color"
    value: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Large", "Red"
    sku_suffix: Mapped[Optional[str]] = mapped_column(String(50))
    
    price_adjustment: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="variants")

    def __repr__(self) -> str:
        return f"<ProductVariant(id={self.id}, name='{self.name}', value='{self.value}')>"


class ProductReview(Base):
    """Product review model"""
    __tablename__ = "product_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 stars
    title: Mapped[Optional[str]] = mapped_column(String(255))
    comment: Mapped[Optional[str]] = mapped_column(Text)
    
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<ProductReview(id={self.id}, rating={self.rating})>"