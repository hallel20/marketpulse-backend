"""
Cart and wishlist database models
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CartItem(Base):
    """Shopping cart item model"""
    __tablename__ = "cart_items"
    
    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='unique_cart_user_product'),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False
    )
    
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    variant_info: Mapped[Optional[str]] = mapped_column(String(255))  # JSON string for variant selection
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

    def __repr__(self) -> str:
        return f"<CartItem(id={self.id}, user_id={self.user_id}, product_id={self.product_id})>"


class WishlistItem(Base):
    """Wishlist item model"""
    __tablename__ = "wishlist_items"
    
    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='unique_wishlist_user_product'),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="wishlist_items")
    product = relationship("Product", back_populates="wishlist_items")

    def __repr__(self) -> str:
        return f"<WishlistItem(id={self.id}, user_id={self.user_id}, product_id={self.product_id})>"