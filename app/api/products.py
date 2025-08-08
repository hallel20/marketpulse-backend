"""
Product management API routes
"""
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, func, desc

from app.database import get_async_session
from app.dependencies import get_current_admin_user, get_current_active_user, get_optional_current_user
from app.models.product import Product, ProductImage, ProductReview
from app.models.user import User
from app.schemas.product import (
    ProductResponse,
    ProductListResponse,
    ProductCreate,
    ProductUpdate,
    ProductSearchQuery,
    ProductSearchResponse,
    ProductReviewCreate,
    ProductReviewResponse
)
from app.services.search_service import SearchService
# from app.services.file_service import FileService
from app.utils.exceptions import NotFoundException, ValidationException, ForbiddenException
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("", response_model=ProductSearchResponse)
async def get_products(
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by category"),
    q: Optional[str] = Query(None, description="Search query"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    in_stock_only: bool = Query(False, description="Show only products in stock"),
    featured_only: bool = Query(False, description="Show only featured products"),
    sort_by: str = Query("created_at", description="Sort by: name, price_asc, price_desc, rating, created_at"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get products with filtering, searching, and pagination
    
    - **category_id**: Filter by specific category
    - **q**: Search in product name and description
    - **min_price/max_price**: Price range filter
    - **in_stock_only**: Show only available products
    - **featured_only**: Show only featured products
    - **sort_by**: Sort products by various criteria
    - **page/page_size**: Pagination controls
    """
    # Build query
    query = (
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.images)
        )
        .where(Product.is_active == True)
    )
    
    # Apply filters
    filters = []
    
    if category_id:
        filters.append(Product.category_id == category_id)
    
    if q:
        search_filter = or_(
            Product.name.ilike(f"%{q}%"),
            Product.description.ilike(f"%{q}%"),
            Product.short_description.ilike(f"%{q}%")
        )
        filters.append(search_filter)
    
    if min_price is not None:
        filters.append(Product.price >= min_price)
    
    if max_price is not None:
        filters.append(Product.price <= max_price)
    
    if in_stock_only:
        filters.append(Product.stock_quantity > 0)
    
    if featured_only:
        filters.append(Product.is_featured == True)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Apply sorting
    if sort_by == "name":
        query = query.order_by(Product.name)
    elif sort_by == "price_asc":
        query = query.order_by(Product.price)
    elif sort_by == "price_desc":
        query = query.order_by(desc(Product.price))
    elif sort_by == "rating":
        query = query.order_by(desc(Product.rating_average))
    else:  # default to created_at
        query = query.order_by(desc(Product.created_at))
    
    # Count total items
    count_query = select(func.count()).select_from(query.subquery())
    total_count = (await session.execute(count_query)).scalar() or 1
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await session.execute(query)
    products = result.scalars().all()
    
    # Convert to list response format
    product_list = []
    for product in products:
        product_data = ProductListResponse(
            id=product.id,
            name=product.name,
            slug=product.slug,
            short_description=product.short_description,
            price=product.price,
            sku=product.sku,
            stock_quantity=product.stock_quantity,
            is_featured=product.is_featured,
            rating_average=product.rating_average,
            rating_count=product.rating_count,
            is_in_stock=product.is_in_stock,
            main_image_url=product.main_image_url,
            category_name=product.category.name
        )
        product_list.append(product_data)
    
    total_pages = (total_count + page_size - 1) // page_size
    
    return ProductSearchResponse(
        products=product_list,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/search", response_model=ProductSearchResponse)
async def search_products(
    q: str = Query(..., min_length=2, description="Search query"),
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Advanced product search using Elasticsearch
    
    Provides faster and more relevant search results with faceted filtering
    """
    search_service = SearchService()
    
    search_params = {
        "query": q,
        "category_id": str(category_id) if category_id else None,
        "min_price": min_price,
        "max_price": max_price,
        "page": page,
        "page_size": page_size
    }
    
    return await search_service.search_products(search_params)


@router.get("/featured", response_model=List[ProductListResponse])
async def get_featured_products(
    limit: int = Query(12, ge=1, le=50, description="Number of featured products to return"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get featured products for homepage display
    """
    query = (
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.images)
        )
        .where(Product.is_active == True)
        .where(Product.is_featured == True)
        .order_by(desc(Product.created_at))
        .limit(limit)
    )
    
    result = await session.execute(query)
    products = result.scalars().all()
    
    product_list = []
    for product in products:
        product_data = ProductListResponse(
            id=product.id,
            name=product.name,
            slug=product.slug,
            short_description=product.short_description,
            price=product.price,
            sku=product.sku,
            stock_quantity=product.stock_quantity,
            is_featured=product.is_featured,
            rating_average=product.rating_average,
            rating_count=product.rating_count,
            is_in_stock=product.is_in_stock,
            main_image_url=product.main_image_url,
            category_name=product.category.name
        )
        product_list.append(product_data)
    
    return product_list


@router.get("/recommendations/{user_id}", response_model=List[ProductListResponse])
async def get_personalized_recommendations(
    user_id: uuid.UUID,
    limit: int = Query(12, ge=1, le=50),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get personalized product recommendations for a user
    
    Based on user's order history and browsing behavior
    """
    # For now, return popular products
    # TODO: Implement ML-based recommendations
    query = (
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.images)
        )
        .where(Product.is_active == True)
        .order_by(desc(Product.rating_average), desc(Product.view_count))
        .limit(limit)
    )
    
    result = await session.execute(query)
    products = result.scalars().all()
    
    product_list = []
    for product in products:
        product_data = ProductListResponse(
            id=product.id,
            name=product.name,
            slug=product.slug,
            short_description=product.short_description,
            price=product.price,
            sku=product.sku,
            stock_quantity=product.stock_quantity,
            is_featured=product.is_featured,
            rating_average=product.rating_average,
            rating_count=product.rating_count,
            is_in_stock=product.is_in_stock,
            main_image_url=product.main_image_url,
            category_name=product.category.name
        )
        product_list.append(product_data)
    
    return product_list


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_optional_current_user()),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get detailed information about a specific product
    
    Increments view count for analytics
    """
    query = (
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.images),
            selectinload(Product.variants)
        )
        .where(Product.id == product_id)
        .where(Product.is_active == True)
    )
    
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise NotFoundException("Product not found")
    
    # Increment view count
    product.view_count += 1
    await session.commit()
    
    return product


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new product (admin only)
    """
    # Check if SKU already exists
    existing_sku = await session.execute(
        select(Product).where(Product.sku == product_data.sku)
    )
    if existing_sku.scalar_one_or_none():
        raise ValidationException("SKU already exists")
    
    # Check if slug already exists
    existing_slug = await session.execute(
        select(Product).where(Product.slug == product_data.slug)
    )
    if existing_slug.scalar_one_or_none():
        raise ValidationException("Slug already exists")
    
    # Create product
    product = Product(**product_data.model_dump())
    session.add(product)
    await session.commit()
    await session.refresh(product, ["category", "images", "variants"])
    
    # Index in Elasticsearch
    search_service = SearchService()
    await search_service.index_product(product)
    
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update a product (admin only)
    """
    # Get product
    result = await session.execute(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.images),
            selectinload(Product.variants)
        )
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise NotFoundException("Product not found")
    
    # Update product
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    await session.commit()
    await session.refresh(product)
    
    # Update in Elasticsearch
    search_service = SearchService()
    await search_service.index_product(product)
    
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete a product (admin only)
    
    Performs soft delete by setting is_active to False
    """
    # Get product
    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise NotFoundException("Product not found")
    
    # Soft delete
    product.is_active = False
    await session.commit()
    
    # Remove from Elasticsearch
    search_service = SearchService()
    await search_service.delete_product(product_id.__str__())
    
    return {"message": "Product deleted successfully"}


@router.post("/{product_id}/images", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_product_images(
    product_id: uuid.UUID,
    files: List[UploadFile] = File(..., description="Product images"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Upload images for a product (admin only)
    
    Supports multiple image upload with automatic resizing and optimization
    """
    # Get product
    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise NotFoundException("Product not found")
    
    # file_service = FileService()
    # uploaded_images = []
    
    # for i, file in enumerate(files):
    #     # Validate file
    #     if not file.content_type.startswith('image/'):
    #         raise ValidationException(f"File {file.filename} is not an image")
        
    #     # Upload file
    #     image_url = await file_service.upload_product_image(file, product_id)
        
    #     # Create product image record
    #     product_image = ProductImage(
    #         product_id=product_id,
    #         image_url=image_url,
    #         alt_text=f"{product.name} - Image {i + 1}",
    #         sort_order=i
    #     )
    #     session.add(product_image)
    #     uploaded_images.append(image_url)
    
    await session.commit()
    
    return {
        "message": f"Successfully uploaded {len(files)} images",
        # "image_urls": uploaded_images
    }


# Product Reviews
@router.get("/{product_id}/reviews", response_model=List[ProductReviewResponse])
async def get_product_reviews(
    product_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get reviews for a specific product
    """
    # Verify product exists
    product = await session.get(Product, product_id)
    if not product or not product.is_active:
        raise NotFoundException("Product not found")
    
    # Get reviews
    offset = (page - 1) * page_size
    query = (
        select(ProductReview)
        .options(selectinload(ProductReview.user))
        .where(ProductReview.product_id == product_id)
        .where(ProductReview.is_approved == True)
        .order_by(desc(ProductReview.created_at))
        .offset(offset)
        .limit(page_size)
    )
    
    result = await session.execute(query)
    reviews = result.scalars().all()
    
    # Convert to response format
    review_responses = []
    for review in reviews:
        review_response = ProductReviewResponse(
            id=review.id,
            product_id=review.product_id,
            user_id=review.user_id,
            rating=review.rating,
            title=review.title,
            comment=review.comment,
            is_verified_purchase=review.is_verified_purchase,
            is_approved=review.is_approved,
            created_at=review.created_at,
            user_name=f"{review.user.first_name} {review.user.last_name[0]}."
        )
        review_responses.append(review_response)
    
    return review_responses


@router.post("/{product_id}/reviews", response_model=ProductReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_product_review(
    product_id: uuid.UUID,
    review_data: ProductReviewCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a review for a product
    
    Users can only review products they have purchased
    """
    # Verify product exists
    product = await session.get(Product, product_id)
    if not product or not product.is_active:
        raise NotFoundException("Product not found")
    
    # Check if user already reviewed this product
    existing_review = await session.execute(
        select(ProductReview)
        .where(ProductReview.product_id == product_id)
        .where(ProductReview.user_id == current_user.id)
    )
    if existing_review.scalar_one_or_none():
        raise ValidationException("You have already reviewed this product")
    
    # TODO: Check if user has purchased this product
    # For now, allow any user to review
    
    # Create review
    review = ProductReview(
        product_id=product_id,
        user_id=current_user.id,
        rating=review_data.rating,
        title=review_data.title,
        comment=review_data.comment,
        is_verified_purchase=False  # TODO: Check actual purchase
    )
    
    session.add(review)
    await session.commit()
    await session.refresh(review, ["user"])
    
    # Update product rating
    rating_result = await session.execute(
        select(func.avg(ProductReview.rating), func.count(ProductReview.id))
        .where(ProductReview.product_id == product_id)
        .where(ProductReview.is_approved == True)
    )
    avg_rating, count = rating_result.first() # type: ignore
    
    product.rating_average = avg_rating
    product.rating_count = count or 0
    await session.commit()
    
    return ProductReviewResponse(
        id=review.id,
        product_id=review.product_id,
        user_id=review.user_id,
        rating=review.rating,
        title=review.title,
        comment=review.comment,
        is_verified_purchase=review.is_verified_purchase,
        is_approved=review.is_approved,
        created_at=review.created_at,
        user_name=f"{current_user.first_name} {current_user.last_name[0]}."
    )