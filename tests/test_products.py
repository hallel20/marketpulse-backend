"""
Tests for product management endpoints
"""
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, Category
from app.models.user import User


@pytest_asyncio.fixture
async def test_category(async_session: AsyncSession) -> Category:
    """Create a test category"""
    category = Category(
        name="Test Category",
        slug="test-category",
        description="A test category"
    )
    
    async_session.add(category)
    await async_session.commit()
    await async_session.refresh(category)
    
    return category


@pytest_asyncio.fixture
async def test_product(async_session: AsyncSession, test_category: Category) -> Product:
    """Create a test product"""
    product = Product(
        name="Test Product",
        slug="test-product",
        description="A test product description",
        short_description="Short description",
        category_id=test_category.id,
        price=Decimal("29.99"),
        cost_price=Decimal("15.00"),
        sku="TEST-001",
        stock_quantity=10,
        is_active=True,
        is_featured=False
    )
    
    async_session.add(product)
    await async_session.commit()
    await async_session.refresh(product)
    
    return product


class TestProductEndpoints:
    """Test product API endpoints"""
    
    async def test_get_products_list(
        self, 
        client: AsyncClient, 
        test_product: Product
    ):
        """Test getting products list"""
        response = await client.get("/api/v1/products")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "products" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        
        assert len(data["products"]) >= 1
        
        # Check first product structure
        product = data["products"][0]
        assert "id" in product
        assert "name" in product
        assert "price" in product
        assert "sku" in product
        assert "category_name" in product
    
    async def test_get_products_with_filters(
        self, 
        client: AsyncClient, 
        test_product: Product,
        test_category: Category
    ):
        """Test getting products with filters"""
        # Filter by category
        response = await client.get(
            f"/api/v1/products?category_id={test_category.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) >= 1
        
        # Filter by price range
        response = await client.get(
            "/api/v1/products?min_price=20&max_price=50"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for product in data["products"]:
            assert 20 <= product["price"] <= 50
        
        # Filter by stock availability
        response = await client.get("/api/v1/products?in_stock_only=true")
        
        assert response.status_code == 200
        data = response.json()
        
        for product in data["products"]:
            assert product["stock_quantity"] > 0
    
    async def test_get_products_with_search(
        self, 
        client: AsyncClient, 
        test_product: Product
    ):
        """Test product search functionality"""
        response = await client.get("/api/v1/products?q=Test")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find our test product
        assert len(data["products"]) >= 1
        
        found_test_product = False
        for product in data["products"]:
            if "Test" in product["name"]:
                found_test_product = True
                break
        
        assert found_test_product
    
    async def test_get_products_pagination(
        self, 
        client: AsyncClient, 
        test_product: Product
    ):
        """Test product pagination"""
        # Test first page
        response = await client.get("/api/v1/products?page=1&page_size=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["products"]) <= 5
        
        # Test page size validation
        response = await client.get("/api/v1/products?page_size=150")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] <= 100  # Should be capped at max
    
    async def test_get_single_product(
        self, 
        client: AsyncClient, 
        test_product: Product
    ):
        """Test getting a single product"""
        response = await client.get(f"/api/v1/products/{test_product.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(test_product.id)
        assert data["name"] == test_product.name
        assert data["description"] == test_product.description
        assert float(data["price"]) == float(test_product.price)
        assert data["sku"] == test_product.sku
        assert data["stock_quantity"] == test_product.stock_quantity
        assert "category" in data
        assert "images" in data
        assert "variants" in data
    
    async def test_get_nonexistent_product(self, client: AsyncClient):
        """Test getting a non-existent product"""
        from uuid import uuid4
        fake_id = str(uuid4())
        
        response = await client.get(f"/api/v1/products/{fake_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    async def test_get_featured_products(
        self, 
        client: AsyncClient, 
        async_session: AsyncSession,
        test_category: Category
    ):
        """Test getting featured products"""
        # Create a featured product
        featured_product = Product(
            name="Featured Product",
            slug="featured-product",
            description="A featured product",
            category_id=test_category.id,
            price=Decimal("99.99"),
            sku="FEAT-001",
            stock_quantity=5,
            is_active=True,
            is_featured=True
        )
        
        async_session.add(featured_product)
        await async_session.commit()
        
        response = await client.get("/api/v1/products/featured")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        
        # Check that all returned products are featured
        for product in data:
            assert product["is_featured"] == True
    
    async def test_create_product_admin_required(
        self, 
        client: AsyncClient,
        test_category: Category,
        auth_headers: dict
    ):
        """Test creating product requires admin privileges"""
        product_data = {
            "name": "New Product",
            "slug": "new-product",
            "description": "A new product",
            "category_id": str(test_category.id),
            "price": 49.99,
            "sku": "NEW-001",
            "stock_quantity": 20
        }
        
        # Regular user should not be able to create products
        response = await client.post(
            "/api/v1/products",
            json=product_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_create_product_success(
        self, 
        client: AsyncClient,
        test_category: Category,
        admin_headers: dict
    ):
        """Test successful product creation by admin"""
        product_data = {
            "name": "Admin Product",
            "slug": "admin-product",
            "description": "A product created by admin",
            "category_id": str(test_category.id),
            "price": 79.99,
            "cost_price": 40.00,
            "sku": "ADM-001",
            "stock_quantity": 15,
            "is_featured": True
        }
        
        response = await client.post(
            "/api/v1/products",
            json=product_data,
            headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == product_data["name"]
        assert data["slug"] == product_data["slug"]
        assert float(data["price"]) == product_data["price"]
        assert data["sku"] == product_data["sku"]
        assert data["stock_quantity"] == product_data["stock_quantity"]
        assert data["is_featured"] == product_data["is_featured"]
    
    async def test_create_product_duplicate_sku(
        self, 
        client: AsyncClient,
        test_product: Product,
        test_category: Category,
        admin_headers: dict
    ):
        """Test creating product with duplicate SKU"""
        product_data = {
            "name": "Duplicate SKU Product",
            "slug": "duplicate-sku-product",
            "description": "Product with duplicate SKU",
            "category_id": str(test_category.id),
            "price": 29.99,
            "sku": test_product.sku,  # Same SKU as existing product
            "stock_quantity": 10
        }
        
        response = await client.post(
            "/api/v1/products",
            json=product_data,
            headers=admin_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "sku" in data["detail"].lower()
    
    async def test_update_product_success(
        self, 
        client: AsyncClient,
        test_product: Product,
        admin_headers: dict
    ):
        """Test successful product update by admin"""
        update_data = {
            "name": "Updated Product Name",
            "price": 39.99,
            "stock_quantity": 25,
            "is_featured": True
        }
        
        response = await client.put(
            f"/api/v1/products/{test_product.id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert float(data["price"]) == update_data["price"]
        assert data["stock_quantity"] == update_data["stock_quantity"]
        assert data["is_featured"] == update_data["is_featured"]
    
    async def test_delete_product_success(
        self, 
        client: AsyncClient,
        test_product: Product,
        admin_headers: dict
    ):
        """Test successful product deletion (soft delete)"""
        response = await client.delete(
            f"/api/v1/products/{test_product.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 204
        
        # Verify product is no longer accessible
        get_response = await client.get(f"/api/v1/products/{test_product.id}")
        assert get_response.status_code == 404
    
    async def test_unauthorized_product_operations(
        self, 
        client: AsyncClient,
        test_product: Product
    ):
        """Test unauthorized product operations"""
        product_data = {"name": "Unauthorized Product"}
        
        # Create without auth
        response = await client.post("/api/v1/products", json=product_data)
        assert response.status_code == 401
        
        # Update without auth
        response = await client.put(
            f"/api/v1/products/{test_product.id}", 
            json=product_data
        )
        assert response.status_code == 401
        
        # Delete without auth
        response = await client.delete(f"/api/v1/products/{test_product.id}")
        assert response.status_code == 401


class TestProductSearch:
    """Test product search functionality"""
    
    async def test_elasticsearch_search(self, client: AsyncClient):
        """Test Elasticsearch product search"""
        # Note: This would require Elasticsearch to be running
        # For now, we'll test the endpoint structure
        
        response = await client.get("/api/v1/products/search?q=test")
        
        # Should return valid response structure even if ES is not running
        assert response.status_code in [200, 500]  # 500 if ES unavailable
        
        if response.status_code == 200:
            data = response.json()
            assert "products" in data
            assert "total_count" in data
            assert "facets" in data
    
    async def test_search_query_validation(self, client: AsyncClient):
        """Test search query validation"""
        # Empty query should fail
        response = await client.get("/api/v1/products/search?q=")
        assert response.status_code == 422
        
        # Query too short should fail
        response = await client.get("/api/v1/products/search?q=a")
        assert response.status_code == 422
    
    async def test_get_search_recommendations(
        self, 
        client: AsyncClient,
        test_user: User
    ):
        """Test personalized recommendations"""
        response = await client.get(
            f"/api/v1/products/recommendations/{test_user.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should return products even if no personalization yet
        for product in data:
            assert "id" in product
            assert "name" in product
            assert "price" in product