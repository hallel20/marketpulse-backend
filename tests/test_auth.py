"""
Tests for authentication endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import AuthService


class TestAuthEndpoints:
    """Test authentication API endpoints"""
    
    async def test_register_user_success(self, client: AsyncClient):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "strongpassword123",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]
        assert data["last_name"] == user_data["last_name"]
        assert "id" in data
        assert data["is_active"] == True
        assert data["is_verified"] == False
    
    async def test_register_user_duplicate_email(
        self, 
        client: AsyncClient, 
        test_user: User
    ):
        """Test registration with existing email"""
        user_data = {
            "email": test_user.email,
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()
    
    async def test_register_user_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email"""
        user_data = {
            "email": "invalid-email",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login"""
        login_data = {
            "email": test_user.email,
            "password": "testpassword"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_invalid_credentials(
        self, 
        client: AsyncClient, 
        test_user: User
    ):
        """Test login with invalid credentials"""
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower()
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = await client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
    
    async def test_refresh_token_success(self, client: AsyncClient, test_user: User):
        """Test successful token refresh"""
        # First login to get tokens
        login_data = {
            "email": test_user.email,
            "password": "testpassword"
        }
        
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        tokens = login_response.json()
        
        # Use refresh token
        refresh_data = {
            "refresh_token": tokens["refresh_token"]
        }
        
        response = await client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token"""
        refresh_data = {
            "refresh_token": "invalid.token.here"
        }
        
        response = await client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
    
    async def test_get_current_user(
        self, 
        client: AsyncClient, 
        test_user: User,
        auth_headers: dict
    ):
        """Test getting current user profile"""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name
        assert data["last_name"] == test_user.last_name
    
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication"""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    async def test_logout_success(
        self, 
        client: AsyncClient, 
        auth_headers: dict
    ):
        """Test successful logout"""
        response = await client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 204
    
    async def test_forgot_password(
        self, 
        client: AsyncClient, 
        test_user: User
    ):
        """Test password reset request"""
        reset_data = {
            "email": test_user.email
        }
        
        response = await client.post("/api/v1/auth/forgot-password", json=reset_data)
        
        assert response.status_code == 204
    
    async def test_forgot_password_nonexistent_email(self, client: AsyncClient):
        """Test password reset for non-existent email"""
        reset_data = {
            "email": "nonexistent@example.com"
        }
        
        response = await client.post("/api/v1/auth/forgot-password", json=reset_data)
        
        # Should still return 204 to prevent email enumeration
        assert response.status_code == 204


class TestAuthService:
    """Test authentication service functionality"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        auth_service = AuthService()
        password = "testpassword123"
        
        # Hash password
        hashed = auth_service.get_password_hash(password)
        
        # Verify correct password
        assert auth_service.verify_password(password, hashed) == True
        
        # Verify incorrect password
        assert auth_service.verify_password("wrongpassword", hashed) == False
    
    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        auth_service = AuthService()
        payload = {"sub": "test@example.com", "user_id": "123"}
        
        # Create access token
        access_token = auth_service.create_access_token(payload)
        assert isinstance(access_token, str)
        
        # Verify access token
        decoded_payload = auth_service.verify_access_token(access_token)
        assert decoded_payload is not None
        assert decoded_payload["sub"] == payload["sub"]
        assert decoded_payload["type"] == "access"
        
        # Create refresh token
        refresh_token = auth_service.create_refresh_token(payload)
        assert isinstance(refresh_token, str)
        
        # Verify refresh token
        decoded_refresh = auth_service.verify_refresh_token(refresh_token)
        assert decoded_refresh is not None
        assert decoded_refresh["sub"] == payload["sub"]
        assert decoded_refresh["type"] == "refresh"
    
    def test_invalid_token_verification(self):
        """Test verification of invalid tokens"""
        auth_service = AuthService()
        
        # Test invalid token
        result = auth_service.verify_access_token("invalid.token.here")
        assert result is None
        
        # Test empty token
        result = auth_service.verify_access_token("")
        assert result is None
    
    async def test_user_authentication(self, async_session: AsyncSession):
        """Test user authentication with database"""
        auth_service = AuthService()
        
        # Create test user
        user = User(
            email="auth@example.com",
            password_hash=auth_service.get_password_hash("password123"),
            first_name="Auth",
            last_name="Test",
            is_active=True
        )
        
        async_session.add(user)
        await async_session.commit()
        
        # Test successful authentication
        authenticated_user = await auth_service.authenticate_user(
            "auth@example.com", 
            "password123", 
            async_session
        )
        assert authenticated_user is not None
        assert authenticated_user.email == "auth@example.com"
        
        # Test failed authentication
        failed_auth = await auth_service.authenticate_user(
            "auth@example.com", 
            "wrongpassword", 
            async_session
        )
        assert failed_auth is None
        
        # Test non-existent user
        no_user = await auth_service.authenticate_user(
            "nonexistent@example.com", 
            "password123", 
            async_session
        )
        assert no_user is None